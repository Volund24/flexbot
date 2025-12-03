import os
from shared.database import get_session, FlexNFT
from sqlalchemy import func

def check_images():
    session = get_session()
    try:
        for slug in ['the_growerz', 'midevils']:
            print(f"--- Checking {slug} ---")
            # Get count
            count = session.query(FlexNFT).filter_by(collection_slug=slug).count()
            print(f"Total items: {count}")
            
            # Get 5 random items with image_url
            items = session.query(FlexNFT).filter_by(collection_slug=slug).limit(5).all()
            for item in items:
                print(f"Mint: {item.mint[:8]}... | Image: {item.image_url}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_images()
