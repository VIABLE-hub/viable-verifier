import segno
import io
import base64


def generate_qr_code(data):
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, scale=10, kind="png")
    buf.seek(0)  # Reset the buffer pointer to the beginning
    val = buf.getvalue()
    img_data = base64.b64encode(val).decode('utf-8')
    return img_data
