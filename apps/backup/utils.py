import os
import zipfile
from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import base64
from hashlib import pbkdf2_hmac
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def derive_key(password: str) -> bytes:
    salt = b"clinic_backup"
    key = pbkdf2_hmac("sha256", password.encode(), salt, 100000, dklen=32)
    return key


def create_backup(include_media: bool = True, password: str | None = None) -> str:
    db_name = os.getenv("POSTGRES_DB", "clinic_db")
    db_user = os.getenv("POSTGRES_USER", "py_exec")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure-password")
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = Path(settings.BACKUP_ROOT)
    backup_root.mkdir(parents=True, exist_ok=True)

    dump_file = backup_root / f"{db_name}_{timestamp}.sql"
    env = os.environ.copy()
    env["PGPASSWORD"] = db_password
    cmd = [
        "pg_dump",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-F",
        "c",
        "-f",
        str(dump_file),
        db_name,
    ]
    subprocess.check_call(cmd, env=env)

    zip_path = backup_root / f"{db_name}_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dump_file, dump_file.name)
        if include_media:
            media_root = Path(settings.MEDIA_ROOT)
            for root, _, files in os.walk(media_root):
                for f in files:
                    full_path = Path(root) / f
                    arcname = Path("media") / full_path.relative_to(media_root)
                    zipf.write(full_path, arcname)
    os.remove(dump_file)

    if password:
        key = derive_key(password)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        data = zip_path.read_bytes()
        enc_data = nonce + aesgcm.encrypt(nonce, data, None)
        enc_path = str(zip_path) + ".enc"
        with open(enc_path, "wb") as f:
            f.write(enc_data)
        zip_path.unlink()
        return enc_path
    return str(zip_path)


def restore_backup(path: str, password: str | None = None) -> None:
    backup_root = Path(settings.BACKUP_ROOT)
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = backup_root / file_path

    if file_path.suffix == ".enc":
        if not password:
            raise ValueError("Password required for encrypted backup")
        key = derive_key(password)
        data = file_path.read_bytes()
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        zip_path = backup_root / file_path.stem
        with open(zip_path, "wb") as f:
            f.write(decrypted)
    else:
        zip_path = file_path

    with zipfile.ZipFile(zip_path, "r") as zipf:
        extract_dir = backup_root / "_restore_tmp"
        zipf.extractall(extract_dir)

    dump_file = next(extract_dir.glob("*.sql"))
    db_name = os.getenv("POSTGRES_DB", "clinic_db")
    db_user = os.getenv("POSTGRES_USER", "py_exec")
    db_password = os.getenv("POSTGRES_PASSWORD", "secure-password")
    db_host = os.getenv("POSTGRES_HOST", "db")
    db_port = os.getenv("POSTGRES_PORT", "5432")

    env = os.environ.copy()
    env["PGPASSWORD"] = db_password
    cmd = [
        "pg_restore",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-d",
        db_name,
        "-c",
        str(dump_file),
    ]
    subprocess.check_call(cmd, env=env)

    media_source = extract_dir / "media"
    if media_source.exists():
        media_root = Path(settings.MEDIA_ROOT)
        for root, _, files in os.walk(media_source):
            for f in files:
                src = Path(root) / f
                dest = media_root / src.relative_to(media_source)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(src.read_bytes())

    shutil.rmtree(extract_dir)


def upload_to_cloud(path: str, provider: str) -> str | None:
    """Upload file to cloud provider and return remote id."""
    if provider == "gdrive":
        try:
            from pydrive.auth import GoogleAuth
            from pydrive.drive import GoogleDrive

            gauth = GoogleAuth()
            creds_file = os.getenv("GDRIVE_CREDENTIALS_FILE")
            if creds_file and os.path.exists(creds_file):
                gauth.LoadCredentialsFile(creds_file)
            else:
                gauth.LocalWebserverAuth()
                if creds_file:
                    gauth.SaveCredentialsFile(creds_file)
            drive = GoogleDrive(gauth)
            f = drive.CreateFile({"title": Path(path).name})
            f.SetContentFile(path)
            f.Upload()
            return f["id"]
        except Exception:
            return None

    if provider == "dropbox":
        try:
            import dropbox

            dbx = dropbox.Dropbox(os.getenv("DROPBOX_TOKEN"))
            dest_path = "/" + Path(path).name
            with open(path, "rb") as fh:
                dbx.files_upload(fh.read(), dest_path)
            return dest_path
        except Exception:
            return None
    return None
