import asyncio
import os
from models import Base, Category, Product
from database import engine, AsyncSessionLocal, get_redis_client
from services import CatalogService

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        cat1 = Category(name="Electronics")
        cat2 = Category(name="Books")
        cat3 = Category(name="Clothing")

        session.add_all([cat1, cat2, cat3])
        await session.flush()

        p1 = Product(name="iPhone 15 Pro", price=999.99, category_id=cat1.id)
        p2 = Product(name="MacBook Pro M3", price=1999.99, category_id=cat1.id)
        p3 = Product(name="Python Clean Code", price=45.00, category_id=cat2.id)
        p4 = Product(name="Nike Air Max", price=120.00, category_id=cat3.id)

        session.add_all([p1, p2, p3, p4])
        await session.commit()
        print("🌱 Database boshlang'ich test ma'lumotlari bilan to'ldirildi!")

async def main():
    print("==========================================================================")
    print("🚀 DATABASE OPTIMIZATION & REDIS CACHE-ASIDE PATTERN DEMO")
    print("==========================================================================\n")

    await init_db()

    redis_client = await get_redis_client()
    catalog_service = CatalogService(redis_client)

    try:
        print("\n--------------------------------------------------------------------------")
        print("📊 1. SQL INDEX VA EXPLAIN QUERY PLAN STRUKTURASI")
        print("--------------------------------------------------------------------------")
        await CatalogService.explain_query_plan("iPhone 15 Pro")

        print("\n--------------------------------------------------------------------------")
        print("🔄 2. N+1 MUAMMOSI VA EAGER LOADING (JOINEDLOAD) YECHIMI")
        print("--------------------------------------------------------------------------")
        await CatalogService.demo_n_plus_1_vs_joinedload()

        print("\n--------------------------------------------------------------------------")
        print("🎯 3. REDIS CACHE-ASIDE PATTERN LIFECYCLE (FETCH, CACHE HIT, INVALIDATION)")
        print("--------------------------------------------------------------------------")
        
        print("\n---> A) Birinchi marta Product #1 so'ralganda (CACHE MISS):")
        prod1 = await catalog_service.get_product_detail(1)
        print("Natija:", prod1)

        print("\n---> B) Ikkinchi marta Product #1 so'ralganda (CACHE HIT):")
        prod1_cached = await catalog_service.get_product_detail(1)
        print("Natija:", prod1_cached)

        print("\n---> C) Product #1 narxini yangilaganda (CACHE INVALIDATION):")
        await catalog_service.update_product_price(1, 1199.99)

        print("\n---> D) Narx o'zgargandan so'ng qayta Product #1 so'ralganda (CACHE MISS):")
        prod1_updated = await catalog_service.get_product_detail(1)
        print("Natija:", prod1_updated)

        print("\n---> E) Yangi narx keshlangandan so'ng yana so'ralganda (CACHE HIT):")
        prod1_updated_cached = await catalog_service.get_product_detail(1)
        print("Natija:", prod1_updated_cached)

        print("\n==========================================================================")
        print("✨ Barcha test va optimizatsiya bosqichlari muvaffaqiyatli yakunlandi!")
        print("==========================================================================")

    finally:
        if hasattr(redis_client, "aclose"):
            await redis_client.aclose()
        elif hasattr(redis_client, "close"):
            await redis_client.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
