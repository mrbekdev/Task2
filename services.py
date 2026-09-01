import json
from typing import Optional, Dict, Any, List
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from models import Product, Category
from database import AsyncSessionLocal

class CatalogService:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def get_product_detail(self, product_id: int) -> Optional[Dict[str, Any]]:
        cache_key = f"product:{product_id}"

        cached_product = await self.redis_client.get(cache_key)
        if cached_product:
            print(f"⚡ [CACHE HIT] Product #{product_id} ma'lumoti Redis'dan qaytarildi!")
            return json.loads(cached_product)

        print(f"🐢 [CACHE MISS] Product #{product_id} ma'lumoti SQL Bazadan qidirilmoqda...")
        async with AsyncSessionLocal() as session:
            stmt = select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
            result = await session.execute(stmt)
            product = result.scalar_one_or_none()

            if not product:
                return None

            product_dict = {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category_id": product.category_id,
                "category_name": product.category.name if product.category else None
            }

            await self.redis_client.set(cache_key, json.dumps(product_dict), ex=300)
            return product_dict

    async def update_product_price(self, product_id: int, new_price: float) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = select(Product).where(Product.id == product_id)
            res = await session.execute(stmt)
            product = res.scalar_one_or_none()

            if not product:
                print(f"❌ Product #{product_id} bazada topilmadi!")
                return False

            old_price = product.price
            product.price = new_price
            await session.commit()
            print(f"📝 Product #{product_id} narxi yangilandi: {old_price} -> {new_price}")

            cache_key = f"product:{product_id}"
            await self.redis_client.delete(cache_key)
            print(f"🗑️ [{cache_key}] keshi tozalandi!")
            return True

    @staticmethod
    async def explain_query_plan(product_name: str):
        async with AsyncSessionLocal() as session:
            explain_stmt = text(f"EXPLAIN QUERY PLAN SELECT * FROM products WHERE name = :name")
            
            result = await session.execute(explain_stmt, {"name": product_name})
            plan = result.fetchall()
            
            print(f"\n🔍 --- EXPLAIN QUERY PLAN (Indekslangan 'name' bo'yicha qidiruv: '{product_name}') ---")
            for row in plan:
                print(f"  Plan: {row}")
            
            explain_cat_stmt = text(f"EXPLAIN QUERY PLAN SELECT * FROM products WHERE category_id = 1")
            result_cat = await session.execute(explain_cat_stmt)
            plan_cat = result_cat.fetchall()
            print(f"🔍 --- EXPLAIN QUERY PLAN (Indekslangan 'category_id' bo'yicha qidiruv) ---")
            for row in plan_cat:
                print(f"  Plan: {row}")

    @staticmethod
    async def demo_n_plus_1_vs_joinedload():
        async with AsyncSessionLocal() as session:
            print("\n🚨 --- 1. N+1 Muammosi Ssenariysi ---")
            print("Agar har bir mahsulotning kategoriyasini alohida-alohida lazy load qilib olsak:")
            print(" - 1-so'rov: barcha products (SELECT * FROM products)")
            print(" - N ta so'rov: har bir product uchun category (SELECT * FROM categories WHERE id = ?)")

            print("\n✅ --- 2. Optimizatsiyalangan Ssenariy (joinedload / JOIN) ---")
            print(" SQLAlchemy joinedload(Product.category) orqali bitta JOIN so'rovi bilan olinadi:")
            print(" SQL: SELECT products.*, categories.* FROM products LEFT OUTER JOIN categories ON categories.id = products.category_id")

            stmt = select(Product).options(joinedload(Product.category))
            result = await session.execute(stmt)
            products = result.scalars().all()
            print(f"\nJami {len(products)} ta mahsulot va ularning kategoriyasi bitta so'rovda muvaffaqiyatli olindi:")
            for p in products:
                print(f"  - [{p.id}] {p.name} | Narxi: ${p.price} | Kategoriya: {p.category.name}")
