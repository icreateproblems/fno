from app.db_pool import get_supabase_client
from app.config import Config

s = get_supabase_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
r = s.table('stories').select('headline, image_url').eq('posted', False).limit(20).execute()

with_images = sum(1 for x in r.data if x.get('image_url'))
without_images = sum(1 for x in r.data if not x.get('image_url'))

print(f"Stories with images: {with_images}")
print(f"Stories without images: {without_images}")
print("\nSample stories:")
for i, x in enumerate(r.data[:10]):
    has_img = bool(x.get('image_url'))
    print(f"{i+1}. {x['headline'][:60]} - {'✅ Has image' if has_img else '❌ No image'}")
