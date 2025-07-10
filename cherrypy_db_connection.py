# File: microserviceNew/cherrypy_db_connection.py

import cherrypy
from peewee import SqliteDatabase
from shared_models import db_a, db_b # Import instance database dari shared_models

class DBConnectionTool(cherrypy.Tool):
    def __init__(self):
        # Menggunakan 'before_handler' sebagai hook point yang lebih umum dan modern
        cherrypy.Tool.__init__(self, 'before_handler', self.open_connection, priority=100)

    def open_connection(self, dbname):
        """Membuka koneksi database berdasarkan nama (db_a atau db_b)."""
        if dbname == 'db_a':
            db_instance = db_a
        elif dbname == 'db_b':
            db_instance = db_b
        else:
            # Ini akan terjadi jika ada kesalahan konfigurasi dbname
            raise ValueError(f"Unknown database name for connection tool: {dbname}")

        if db_instance.is_closed():
            db_instance.connect()
        # Menyimpan instance db di cherrypy.request agar bisa diakses oleh handler
        cherrypy.request.db = db_instance

    def close_connection(self):
        """Menutup koneksi database."""
        # Pastikan ada objek db di request dan belum ditutup sebelum mencoba menutupnya
        if hasattr(cherrypy.request, 'db') and not cherrypy.request.db.is_closed():
            cherrypy.request.db.close()

# Daftarkan tool ini ke CherryPy di bawah nama 'db_connection'
cherrypy.tools.db_connection = DBConnectionTool()

# Tambahkan hook untuk menutup koneksi setelah permintaan selesai
# Ini memastikan koneksi database ditutup dengan bersih
cherrypy.tools.db_connection.on_end_request = cherrypy.tools.db_connection.close_connection