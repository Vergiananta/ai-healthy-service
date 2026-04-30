from sqlalchemy.orm import Session
from app.models.master import MstTypeFood, MstAlergenFood, MstTypeDessert


def seed_master_data(db: Session):
    """
    Seed master data jika tabel masih kosong.
    Dipanggil otomatis saat aplikasi startup.
    """
    _seed_type_food(db)
    _seed_alergen_food(db)
    _seed_type_dessert(db)


def _seed_type_food(db: Session):
    if db.query(MstTypeFood).count() > 0:
        return

    data = [
        MstTypeFood(name="Western", description="Masakan Barat seperti pasta, steak, burger"),
        MstTypeFood(name="Southeast Asia", description="Masakan Asia Tenggara seperti nasi goreng, rendang, pho"),
        MstTypeFood(name="Middle East", description="Masakan Timur Tengah seperti kebab, hummus, shawarma"),
        MstTypeFood(name="East Asia", description="Masakan Asia Timur seperti sushi, dim sum, ramen"),
        MstTypeFood(name="Latin America", description="Masakan Amerika Latin seperti tacos, empanada, ceviche"),
        MstTypeFood(name="Lainnya", description="Tipe masakan lainnya"),
    ]
    db.add_all(data)
    db.commit()
    print("[Seeder] MstTypeFood seeded.")


def _seed_alergen_food(db: Session):
    if db.query(MstAlergenFood).count() > 0:
        return

    data = [
        MstAlergenFood(name="Gluten", description="Terdapat pada gandum, rye, barley"),
        MstAlergenFood(name="Susu / Dairy", description="Produk berbahan dasar susu sapi"),
        MstAlergenFood(name="Kacang-kacangan", description="Kacang tanah, almond, walnut, dll"),
        MstAlergenFood(name="Seafood", description="Ikan, udang, cumi, kerang, dll"),
        MstAlergenFood(name="Telur", description="Telur ayam atau telur lainnya"),
        MstAlergenFood(name="Kedelai / Soy", description="Produk berbahan dasar kedelai"),
        MstAlergenFood(name="Sesame", description="Biji wijen dan produk turunannya"),
        MstAlergenFood(name="Tidak Ada", description="Tidak memiliki alergi makanan"),
    ]
    db.add_all(data)
    db.commit()
    print("[Seeder] MstAlergenFood seeded.")


def _seed_type_dessert(db: Session):
    if db.query(MstTypeDessert).count() > 0:
        return

    data = [
        MstTypeDessert(name="Buah", description="Buah-buahan segar atau olahan"),
        MstTypeDessert(name="Kue Manis", description="Kue, cake, brownies, dan sejenisnya"),
        MstTypeDessert(name="Kue Asin", description="Crackers, keripik, dan kue gurih"),
        MstTypeDessert(name="Es Krim", description="Ice cream, gelato, sorbet"),
        MstTypeDessert(name="Cokelat", description="Cokelat batang, praline, truffle"),
        MstTypeDessert(name="Pudding", description="Pudding susu, jelly, panna cotta"),
        MstTypeDessert(name="Minuman Manis", description="Bubble tea, milkshake, smoothie"),
        MstTypeDessert(name="Lainnya", description="Jenis dessert lainnya"),
    ]
    db.add_all(data)
    db.commit()
    print("[Seeder] MstTypeDessert seeded.")
