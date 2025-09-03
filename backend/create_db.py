from backend.database import Base, engine
from backend.models import dream, image

print("📦 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Done.")
