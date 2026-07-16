from src.real_estate_backend.core.database import SessionLocal
from src.real_estate_backend.customers.model import Customer
from src.real_estate_backend.properties.model import Property
from src.real_estate_backend.leads.model import Lead, LeadStatus


def seed():
    db = SessionLocal()

    try:
        # ── Customers ──────────────────────────────────────────
        customers = [
            Customer(full_name="Ahmed Khan", email="ahmed@test.com", phone="03001111111", is_active=True),
            Customer(full_name="Sara Ali", email="sara@test.com", phone="03002222222", is_active=True),
            Customer(full_name="Bilal Raza", email="bilal@test.com", phone="03003333333", is_active=False),
            Customer(full_name="Fatima Noor", email="fatima@test.com", phone="03004444444", is_active=True),
            Customer(full_name="Usman Tariq", email="usman@test.com", phone="03005555555", is_active=True),
            Customer(full_name="Zara Sheikh", email="zara@test.com", phone="03006666666", is_active=True),
            Customer(full_name="Hassan Malik", email="hassan@test.com", phone="03007777777", is_active=False),
            Customer(full_name="Ayesha Butt", email="ayesha@test.com", phone="03008888888", is_active=True),
            Customer(full_name="Imran Qureshi", email="imran@test.com", phone="03009999999", is_active=True),
            Customer(full_name="Nadia Hussain", email="nadia@test.com", phone="03011111111", is_active=False),
        ]
        db.add_all(customers)
        db.flush()

        # ── Properties ─────────────────────────────────────────
        properties = [
            Property(title="Modern Apartment", city="Lahore", address="12 Gulberg St", price=5000000, bedrooms=3, bathrooms=2, area_sqft=1200, is_available=True),
            Property(title="Family House", city="Karachi", address="45 DHA Phase 5", price=12000000, bedrooms=5, bathrooms=4, area_sqft=3000, is_available=True),
            Property(title="Studio Flat", city="Islamabad", address="7 F-10 Markaz", price=2500000, bedrooms=1, bathrooms=1, area_sqft=600, is_available=True),
            Property(title="Luxury Villa", city="Lahore", address="99 Canal Road", price=35000000, bedrooms=6, bathrooms=5, area_sqft=6000, is_available=False),
            Property(title="Commercial Plaza", city="Faisalabad", address="22 Peoples Colony", price=18000000, bedrooms=0, bathrooms=3, area_sqft=4000, is_available=True),
            Property(title="Corner House", city="Karachi", address="33 Clifton Block 4", price=22000000, bedrooms=4, bathrooms=3, area_sqft=2500, is_available=True),
            Property(title="Penthouse Suite", city="Islamabad", address="5 Blue Area Tower", price=45000000, bedrooms=4, bathrooms=4, area_sqft=5000, is_available=True),
            Property(title="Budget Flat", city="Lahore", address="77 Johar Town", price=1800000, bedrooms=2, bathrooms=1, area_sqft=800, is_available=False),
            Property(title="Farm House", city="Multan", address="Plot 9 Bosan Road", price=28000000, bedrooms=5, bathrooms=4, area_sqft=8000, is_available=True),
            Property(title="Office Space", city="Faisalabad", address="44 Susan Road", price=9500000, bedrooms=0, bathrooms=2, area_sqft=2000, is_available=True),
        ]
        db.add_all(properties)
        db.flush()

        # ── Leads ──────────────────────────────────────────────
        leads = [
            Lead(customer_id=customers[0].id, property_id=properties[0].id, status=LeadStatus.NEW, agent_id="agent_001", notes="Very interested, follow up Monday"),
            Lead(customer_id=customers[1].id, property_id=properties[1].id, status=LeadStatus.CONTACTED, agent_id="agent_002", notes="Requested site visit"),
            Lead(customer_id=customers[2].id, property_id=properties[2].id, status=LeadStatus.QUALIFIED, agent_id="agent_001", notes="Budget confirmed"),
            Lead(customer_id=customers[3].id, property_id=properties[3].id, status=LeadStatus.CLOSED, agent_id="agent_003", notes="Deal closed successfully"),
            Lead(customer_id=customers[4].id, property_id=properties[4].id, status=LeadStatus.LOST, agent_id="agent_002", notes="Client went with another property"),
            Lead(customer_id=customers[5].id, property_id=properties[5].id, status=LeadStatus.NEW, agent_id="agent_003", notes="Seen the listing online, wants more info"),
            Lead(customer_id=customers[6].id, property_id=properties[6].id, status=LeadStatus.CONTACTED, agent_id="agent_001", notes="Called twice, no response yet"),
            Lead(customer_id=customers[7].id, property_id=properties[7].id, status=LeadStatus.QUALIFIED, agent_id="agent_002", notes="Loan pre-approved, ready to move"),
            Lead(customer_id=customers[8].id, property_id=properties[8].id, status=LeadStatus.NEW, agent_id="agent_003", notes="Referred by existing client"),
            Lead(customer_id=customers[9].id, property_id=properties[9].id, status=LeadStatus.LOST, agent_id="agent_001", notes="Budget too low for this property"),
        ]
        db.add_all(leads)

        db.commit()
        print("Seed data inserted successfully")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()