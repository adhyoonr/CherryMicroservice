# File: microserviceNew/shared_models.py

from peewee import *
import os

# Definisikan direktori induk (tempat shared_models.py ini berada)
# Ini akan mengarahkan database ke folder 'microserviceNew/'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inisialisasi database SQLite untuk CarAPI dan UserAPI
# db_a.sqlite akan dibuat di direktori induk: microserviceNew/db_a.sqlite
db_a = SqliteDatabase(os.path.join(BASE_DIR, 'db_a.sqlite'))

# Inisialisasi database SQLite untuk AdminAPI
# db_b.sqlite akan dibuat di direktori induk: microserviceNew/db_b.sqlite
db_b = SqliteDatabase(os.path.join(BASE_DIR, 'db_b.sqlite'))

# --- Base Models ---
# Model dasar untuk tabel yang akan menggunakan db_a
class BaseModelA(Model):
    class Meta:
        database = db_a

# Model dasar untuk tabel yang akan menggunakan db_b
class BaseModelB(Model):
    class Meta:
        database = db_b

# --- Definisi Tabel ---
# Tabel untuk CarAPI (menggunakan db_a)
class TBCarsWeb(BaseModelA):
    id = AutoField()
    carname = CharField(unique=True)
    carbrand = CharField()
    carmodel = CharField()
    carprice = DecimalField(max_digits=10, decimal_places=2)
    description = TextField(null=True)

    class Meta:
        # Menambahkan indeks untuk pencarian cepat jika diperlukan
        indexes = (
            (('carname', 'carbrand', 'carmodel'), False),
        )

# Tabel untuk UserAPI (juga menggunakan db_a)
class User(BaseModelA):
    id = AutoField()
    username = CharField(unique=True)
    email = CharField(unique=True)
    fullname = CharField(null=True)

    class Meta:
        indexes = (
            (('username', 'email'), True), # True untuk unique index
        )

# Tabel untuk AdminAPI (menggunakan db_b)
class Admin(BaseModelB):
    id = AutoField()
    username = CharField(unique=True)
    email = CharField(unique=True)
    role = CharField(null=True)

    class Meta:
        indexes = (
            (('username', 'email'), True), # True untuk unique index
        )

# --- Fungsi Inisialisasi Database ---
# Fungsi ini akan membuat tabel jika belum ada.
# Penting: Fungsi ini HANYA untuk membuat struktur tabel.
# Koneksi per request akan diatur oleh tools CherryPy di masing-masing app.py.
def initialize_db_a_tables():
    """Menghubungkan ke db_a dan membuat tabel TBCarsWeb dan User jika belum ada."""
    db_a.connect()
    db_a.create_tables([TBCarsWeb, User], safe=True)
    if not db_a.is_closed():
        db_a.close() # Tutup koneksi setelah pembuatan tabel selesai

def initialize_db_b_tables():
    """Menghubungkan ke db_b dan membuat tabel Admin jika belum ada."""
    db_b.connect()
    db_b.create_tables([Admin], safe=True)
    if not db_b.is_closed():
        db_b.close() # Tutup koneksi setelah pembuatan tabel selesai

# Bagian ini akan berjalan jika shared_models.py dieksekusi langsung
# Berguna untuk menginisialisasi database secara manual tanpa menjalankan CherryPy
if __name__ == '__main__':
    print("Initializing databases...")
    initialize_db_a_tables()
    initialize_db_b_tables()
    print("Database db_a.sqlite and db_b.sqlite initialized with all tables in the root directory.")
    print(f"Check your '{BASE_DIR}' directory for 'db_a.sqlite' and 'db_b.sqlite'.")