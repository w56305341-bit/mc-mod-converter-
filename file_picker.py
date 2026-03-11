"""
File Picker Utility
Android: Uses Intent ACTION_GET_CONTENT (Scoped Storage safe).
Desktop: tkinter fallback (handled in main_screen.py).
"""

from kivy.utils import platform


def pick_file(callback):
    """
    Opens the system file picker.
    callback(path: str) is called with the selected file path.
    """
    if platform == "android":
        _android_pick(callback)
    else:
        # Desktop fallback – the UI layer handles this
        callback(None)


def _android_pick(callback):
    """
    Uses Android's Storage Access Framework (SAF) via ACTION_GET_CONTENT.
    Works on Android 10+ Scoped Storage without MANAGE_ALL_FILES.
    """
    try:
        from android import activity, mActivity
        from jnius import autoclass, cast

        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        # Allow multiple MIME types
        intent.putExtra(
            Intent.EXTRA_MIME_TYPES,
            [
                "application/zip",
                "application/octet-stream",
                "application/x-zip-compressed",
            ],
        )
        intent.putExtra(Intent.EXTRA_LOCAL_ONLY, True)

        REQUEST_CODE = 9001

        def on_activity_result(request_code, result_code, data):
            activity.unbind(on_activity_result=on_activity_result)
            RESULT_OK = -1  # Activity.RESULT_OK
            if request_code == REQUEST_CODE and result_code == RESULT_OK and data:
                uri = data.getData()
                real_path = _resolve_uri(uri)
                callback(real_path)
            else:
                callback(None)

        activity.bind(on_activity_result=on_activity_result)
        mActivity.startActivityForResult(intent, REQUEST_CODE)

    except Exception as e:
        print(f"Android file picker error: {e}")
        callback(None)


def _resolve_uri(uri) -> str:
    """
    Converts a content:// URI to a real file path.
    Handles Scoped Storage on Android 10–14.
    """
    try:
        from jnius import autoclass
        from android import mActivity

        # Try to get the real path from the URI
        context = mActivity.getApplicationContext()
        Uri = autoclass("android.net.Uri")
        DocumentsContract = autoclass("android.provider.DocumentsContract")
        MediaStore = autoclass("android.provider.MediaStore")
        Build = autoclass("android.os.Build")

        scheme = uri.getScheme()

        # ── content:// URI ──
        if scheme == "content":
            # Check if it's a document URI
            if DocumentsContract.isDocumentUri(context, uri):
                authority = uri.getAuthority()

                # External storage provider
                if authority == "com.android.externalstorage.documents":
                    doc_id = DocumentsContract.getDocumentId(uri)
                    doc_type, rel_path = doc_id.split(":", 1)
                    if doc_type.upper() == "PRIMARY":
                        from android.storage import primary_external_storage_path
                        return f"{primary_external_storage_path()}/{rel_path}"

                # Downloads provider
                elif authority == "com.android.providers.downloads.documents":
                    doc_id = DocumentsContract.getDocumentId(uri)
                    if doc_id.startswith("raw:"):
                        return doc_id[4:]
                    # Numeric ID → resolve via content query
                    return _query_content_uri(
                        context,
                        autoclass("android.net.Uri").parse(
                            f"content://downloads/public_downloads/{doc_id}"
                        ),
                    )

            # Generic content URI – copy to cache
            return _copy_to_cache(context, uri)

        # ── file:// URI ──
        elif scheme == "file":
            return uri.getPath()

        return str(uri)

    except Exception as e:
        print(f"URI resolve error: {e}")
        # Last resort: copy to cache
        try:
            from android import mActivity
            return _copy_to_cache(mActivity.getApplicationContext(), uri)
        except Exception:
            return str(uri)


def _query_content_uri(context, uri) -> str:
    """Query MediaStore for actual file path."""
    try:
        from jnius import autoclass
        projection = ["_data"]
        cursor = context.getContentResolver().query(uri, projection, None, None, None)
        if cursor and cursor.moveToFirst():
            col = cursor.getColumnIndexOrThrow("_data")
            path = cursor.getString(col)
            cursor.close()
            return path
    except Exception as e:
        print(f"Content URI query error: {e}")
    return str(uri)


def _copy_to_cache(context, uri) -> str:
    """
    Copies a content:// file into the app cache directory.
    Reliable fallback for all Android versions.
    """
    import os
    try:
        from jnius import autoclass
        cache_dir = context.getCacheDir().getAbsolutePath()
        filename = _get_filename_from_uri(context, uri) or "mod_file.zip"
        dest_path = os.path.join(cache_dir, filename)

        input_stream = context.getContentResolver().openInputStream(uri)
        FileOutputStream = autoclass("java.io.FileOutputStream")
        out = FileOutputStream(dest_path)

        buffer = autoclass("java.lang.reflect.Array").newInstance(
            autoclass("java.lang.Byte").TYPE, 8192
        )
        while True:
            n = input_stream.read(buffer)
            if n == -1:
                break
            out.write(buffer, 0, n)

        input_stream.close()
        out.close()
        return dest_path

    except Exception as e:
        print(f"Cache copy error: {e}")
        return str(uri)


def _get_filename_from_uri(context, uri) -> str | None:
    """Extract display name from a content URI."""
    try:
        from jnius import autoclass
        OpenableColumns = autoclass("android.provider.OpenableColumns")
        cursor = context.getContentResolver().query(uri, None, None, None, None)
        if cursor and cursor.moveToFirst():
            col = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if col >= 0:
                name = cursor.getString(col)
                cursor.close()
                return name
    except Exception:
        pass
    return None
