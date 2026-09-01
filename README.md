# 3-Loyiha: Database Optimizatsiya va Redis Cache-Aside Servisi

Ushbu loyiha SQL indeksi, `EXPLAIN QUERY PLAN` / `EXPLAIN ANALYZE`, N+1 muammosini hal qilish hamda Redis Cache-Aside kesh patterned integratsiyasini to'liq qamrab oladi.

---

## 📌 Asosiy Konsepsiyalar va Optimizatsiyalar

### 1. SQL Indekslar (Indexes)
`Product` modelida `name` va `category_id` ustunlariga `index=True` berilgan.
- Indekssiz qidiruv: `SCAN TABLE products` (Barcha qatorlarni ko'rib chiqadi - O(N)).
- Indeksli qidiruv: `SEARCH TABLE products USING INDEX ix_products_name` (B-Tree orqali tezkor qidiruv - O(log N)).

### 2. N+1 Muammosi va `joinedload` (Eager Loading)
- **N+1 Muammosi:** Har bir mahsulot va uning kategoriyasini olish uchun 1 ta asosiy SQL so'rovi va har bir mahsulot uchun N ta alohida SQL so'rovi yuborilishi (`1 + N`).
- **Yechim:** SQLAlchemy `options(joinedload(Product.category))` yordamida bitta `LEFT OUTER JOIN` so'rovi orqali barcha bog'liq ma'lumotlar 1 ta SQL so'rovida olinadi.

### 3. Redis Cache-Aside Pattern Lifecycle
1. **Cache Check (Hit/Miss):** Kalit (`product:{id}`) Redis'dan izlanadi.
2. **Cache Hit:** Agar mavjud bo'lsa, ma'lumot darhol Redis'dan qaytariladi (SQL bazaga so'rov yuborilmaydi).
3. **Cache Miss:** Keshda bo'lmasa, ma'lumot SQL Bazadan optimallashtirilgan query bilan olinadi va Redis'ga 300 soniyalik TTL (`ex=300`) bilan yoziladi.
4. **Cache Invalidation:** Narx yoki boshqa ustunlar yangilanganda (`update_product_price`), keshdagi eski ma me'lumot `redis_client.delete(key)` orqali o'chiriladi.

---

## 📁 Loyiha Tarkibi

- [`models.py`](file:///Users/ismadbek/Desktop/Malaka/Task2/models.py) - `Category` va `Product` modellari, SQL indeksi hamda ORM relationship.
- [`database.py`](file:///Users/ismadbek/Desktop/Malaka/Task2/database.py) - Async Engine (SQLite), SessionMaker va Redis Client (Real Redis / FakeRedis fallback).
- [`services.py`](file:///Users/ismadbek/Desktop/Malaka/Task2/services.py) - `CatalogService` (Cache-Aside, Query Plan EXPLAIN va N+1 yechimi).
- [`main.py`](file:///Users/ismadbek/Desktop/Malaka/Task2/main.py) - Loyihaning to'liq ish faoliyatini namoyish etuvchi script.

---

## 🚀 Qanday Ishga Tushiriladi?

```bash
# 1. Bog'liqliklar install qilinadi
python3 -m pip install sqlalchemy aiosqlite redis fakeredis greenlet

# 2. Asosiy dastur ishga tushiriladi
python3 main.py
```
# Task2
