"""
Seed script — populates the database with realistic test data.

Usage:
    python seed.py

Creates:
- 2 agent accounts (buyer_agent, seller_agent) + 3 regular users
- 6 categories
- 12 listings across sellers (various statuses)
- Bids, counter-offers, conversations, messages
- Transactions in various states
- Wallet balances for buyers
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.common.db import async_session_factory, engine
from app.common.models.base import Base
from app.common.models.listing import Category, Listing, listing_categories
from app.common.models.negotiation import Bid, Conversation, Message
from app.common.models.transaction import Transaction
from app.common.models.user import User, Wallet
from app.common.types.listings import Condition, ListingStatus
from app.common.types.negotiations import ActorType, BidStatus, BidType
from app.common.types.transactions import TransactionStatus
from app.integrations.embeddings import generate_embedding
from app.modules.users.service import hash_password

# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

PASSWORD = "Test1234!"  # shared password for all seed accounts

USERS = [
    {
        "email": "buyer-agent@moltplaats.nl",
        "display_name": "Buyer Agent",
        "latitude": 52.3676,
        "longitude": 4.9041,
        "is_verified": True,
        "wallet_balance": 500_00,  # €500 in cents
    },
    {
        "email": "seller-agent@moltplaats.nl",
        "display_name": "Seller Agent",
        "latitude": 52.0907,
        "longitude": 5.1214,
        "is_verified": True,
        "wallet_balance": 100_00,
    },
    {
        "email": "alice@example.com",
        "display_name": "Alice Jansen",
        "latitude": 51.9225,
        "longitude": 4.4792,
        "is_verified": True,
        "wallet_balance": 300_00,
    },
    {
        "email": "bob@example.com",
        "display_name": "Bob de Vries",
        "latitude": 52.3702,
        "longitude": 4.8952,
        "is_verified": True,
        "wallet_balance": 150_00,
    },
    {
        "email": "charlie@example.com",
        "display_name": "Charlie Bakker",
        "latitude": 51.4416,
        "longitude": 5.4697,
        "is_verified": False,
        "wallet_balance": 0,
    },
]

CATEGORIES = [
    {"name": "Electronics", "slug": "electronics"},
    {"name": "Furniture", "slug": "furniture"},
    {"name": "Clothing", "slug": "clothing"},
    {"name": "Books", "slug": "books"},
    {"name": "Sports & Outdoors", "slug": "sports-outdoors"},
    {"name": "Home & Garden", "slug": "home-garden"},
]

# (seller_email, title, description, price_cents, condition, status, category_slugs)
LISTINGS = [
    # Seller Agent listings
    (
        "seller-agent@moltplaats.nl",
        "iPhone 14 Pro 128GB",
        "Space Black, excellent condition, always used with case and screen protector. Battery health 94%. Comes with original box and charger.",
        650_00,
        Condition.LIKE_NEW,
        ListingStatus.ACTIVE,
        ["electronics"],
    ),
    (
        "seller-agent@moltplaats.nl",
        "IKEA KALLAX Shelf Unit",
        "White, 4x4 compartments. Minor scratch on the side, barely noticeable. Disassembled for easy transport.",
        45_00,
        Condition.GOOD,
        ListingStatus.ACTIVE,
        ["furniture", "home-garden"],
    ),
    (
        "seller-agent@moltplaats.nl",
        "Sony WH-1000XM5 Headphones",
        "Silver, noise cancelling. Used for 6 months, perfect working condition.",
        180_00,
        Condition.LIKE_NEW,
        ListingStatus.ACTIVE,
        ["electronics"],
    ),
    (
        "seller-agent@moltplaats.nl",
        "Draft Listing - Test",
        "This is a draft listing for testing purposes.",
        10_00,
        Condition.NEW,
        ListingStatus.DRAFT,
        ["electronics"],
    ),
    # Alice listings
    (
        "alice@example.com",
        "Vintage Leather Jacket",
        "Genuine leather, size M. Beautiful patina from years of wear. Classic biker style.",
        85_00,
        Condition.GOOD,
        ListingStatus.ACTIVE,
        ["clothing"],
    ),
    (
        "alice@example.com",
        "Complete Harry Potter Box Set",
        "All 7 books, hardcover UK editions. Some wear on spines but pages are clean.",
        55_00,
        Condition.FAIR,
        ListingStatus.ACTIVE,
        ["books"],
    ),
    (
        "alice@example.com",
        "Yoga Mat + Blocks Set",
        "Manduka PRO mat (6mm) with two cork blocks. Used gently for about a year.",
        40_00,
        Condition.GOOD,
        ListingStatus.ACTIVE,
        ["sports-outdoors"],
    ),
    # Bob listings
    (
        "bob@example.com",
        "Herman Miller Aeron Chair",
        "Size B, fully loaded. Remastered version. Small mark on armrest. Best office chair you'll ever sit in.",
        450_00,
        Condition.GOOD,
        ListingStatus.ACTIVE,
        ["furniture"],
    ),
    (
        "bob@example.com",
        "Nintendo Switch OLED + Games",
        "White model with 3 games: Zelda TOTK, Mario Kart 8, Animal Crossing. All in original cases.",
        280_00,
        Condition.LIKE_NEW,
        ListingStatus.ACTIVE,
        ["electronics"],
    ),
    (
        "bob@example.com",
        "Garden Tool Set",
        "Spade, fork, trowel, pruning shears. Stainless steel. Barely used, moving to apartment.",
        35_00,
        Condition.LIKE_NEW,
        ListingStatus.ACTIVE,
        ["home-garden"],
    ),
    # Charlie listings
    (
        "charlie@example.com",
        "Mountain Bike - Trek Marlin 7",
        "2024 model, size L. Ridden about 500km on trails. Hydraulic disc brakes, 1x12 drivetrain.",
        620_00,
        Condition.LIKE_NEW,
        ListingStatus.ACTIVE,
        ["sports-outdoors"],
    ),
    (
        "charlie@example.com",
        "Standing Desk - Flexispot E7",
        "140x70cm bamboo top. Dual motor, programmable heights. Cable tray included.",
        320_00,
        Condition.GOOD,
        ListingStatus.ACTIVE,
        ["furniture"],
    ),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already has data — skipping seed.")
            return

        # ----- Users & Wallets -----
        users: dict[str, User] = {}
        hashed = hash_password(PASSWORD)

        for u in USERS:
            user = User(
                email=u["email"],
                hashed_password=hashed,
                display_name=u["display_name"],
                latitude=u["latitude"],
                longitude=u["longitude"],
                is_active=True,
                is_verified=u["is_verified"],
            )
            session.add(user)
            await session.flush()
            users[u["email"]] = user

            wallet = Wallet(
                user_id=user.id,
                balance=u["wallet_balance"],
                held_balance=0,
            )
            session.add(wallet)

        await session.flush()
        print(f"Created {len(users)} users with wallets")

        # ----- Categories -----
        categories: dict[str, Category] = {}
        for c in CATEGORIES:
            cat = Category(name=c["name"], slug=c["slug"])
            session.add(cat)
            await session.flush()
            categories[c["slug"]] = cat

        print(f"Created {len(categories)} categories")

        # ----- Listings -----
        listings: list[Listing] = []
        for seller_email, title, desc, price, condition, status, cat_slugs in LISTINGS:
            embedding = await generate_embedding(f"{title}\n{desc}")
            listing = Listing(
                seller_id=users[seller_email].id,
                title=title,
                description=desc,
                price=price,
                condition=condition,
                status=status,
                embedding=embedding,
            )
            session.add(listing)
            await session.flush()

            for slug in cat_slugs:
                await session.execute(
                    listing_categories.insert().values(
                        listing_id=listing.id,
                        category_id=categories[slug].id,
                    )
                )

            listings.append(listing)

        await session.flush()
        print(f"Created {len(listings)} listings")

        # ----- Helper to find active listings -----
        active = [l for l in listings if l.status == ListingStatus.ACTIVE]

        # ----- Bids & Conversations -----

        # Buyer Agent bids on Alice's leather jacket
        jacket = next(l for l in active if "Leather Jacket" in l.title)
        bid1 = Bid(
            listing_id=jacket.id,
            bidder_id=users["buyer-agent@moltplaats.nl"].id,
            amount=70_00,
            bid_type=BidType.BUYER,
            status=BidStatus.PENDING,
        )
        session.add(bid1)
        await session.flush()

        conv1 = Conversation(
            listing_id=jacket.id,
            buyer_id=users["buyer-agent@moltplaats.nl"].id,
        )
        session.add(conv1)
        await session.flush()

        for body in [
            "Hi! I'm interested in the leather jacket. Would you take €70?",
            "Bid placed: 7000",
        ]:
            session.add(
                Message(
                    conversation_id=conv1.id,
                    actor_type=ActorType.USER,
                    sender_id=users["buyer-agent@moltplaats.nl"].id,
                    body=body,
                    bid_id=bid1.id if "Bid placed" in body else None,
                )
            )

        # Alice counters at €80
        bid1.status = BidStatus.COUNTERED
        bid1_counter = Bid(
            listing_id=jacket.id,
            bidder_id=users["alice@example.com"].id,
            amount=80_00,
            bid_type=BidType.SELLER,
            status=BidStatus.PENDING,
            parent_bid_id=bid1.id,
        )
        session.add(bid1_counter)
        await session.flush()

        session.add(
            Message(
                conversation_id=conv1.id,
                actor_type=ActorType.USER,
                sender_id=users["alice@example.com"].id,
                body="Thanks for the offer! I can do €80, the leather is really premium quality.",
            )
        )
        session.add(
            Message(
                conversation_id=conv1.id,
                actor_type=ActorType.USER,
                sender_id=users["alice@example.com"].id,
                body="Counter-offer: 8000",
                bid_id=bid1_counter.id,
            )
        )

        # Bob bids on Seller Agent's iPhone — accepted → transaction
        iphone = next(l for l in active if "iPhone" in l.title)
        bid2 = Bid(
            listing_id=iphone.id,
            bidder_id=users["bob@example.com"].id,
            amount=600_00,
            bid_type=BidType.BUYER,
            status=BidStatus.ACCEPTED,
        )
        session.add(bid2)
        await session.flush()

        conv2 = Conversation(listing_id=iphone.id, buyer_id=users["bob@example.com"].id)
        session.add(conv2)
        await session.flush()

        for body, sender in [
            ("Would you do €600? Can pick up this weekend.", "bob@example.com"),
            ("Bid placed: 60000", "bob@example.com"),
            ("Deal! I'll accept.", "seller-agent@moltplaats.nl"),
            ("Bid accepted", "seller-agent@moltplaats.nl"),
        ]:
            session.add(
                Message(
                    conversation_id=conv2.id,
                    actor_type=ActorType.USER,
                    sender_id=users[sender].id,
                    body=body,
                )
            )

        iphone.status = ListingStatus.SOLD

        txn1 = Transaction(
            bid_id=bid2.id,
            buyer_id=users["bob@example.com"].id,
            seller_id=users["seller-agent@moltplaats.nl"].id,
            amount=600_00,
            status=TransactionStatus.PENDING_ESCROW,
        )
        session.add(txn1)

        # Buyer Agent bids on Bob's Switch — accepted, escrowed
        switch = next(l for l in active if "Switch" in l.title)
        bid3 = Bid(
            listing_id=switch.id,
            bidder_id=users["buyer-agent@moltplaats.nl"].id,
            amount=260_00,
            bid_type=BidType.BUYER,
            status=BidStatus.ACCEPTED,
        )
        session.add(bid3)
        await session.flush()

        conv3 = Conversation(
            listing_id=switch.id, buyer_id=users["buyer-agent@moltplaats.nl"].id
        )
        session.add(conv3)
        await session.flush()

        session.add(
            Message(
                conversation_id=conv3.id,
                actor_type=ActorType.USER,
                sender_id=users["buyer-agent@moltplaats.nl"].id,
                body="Bid placed: 26000",
                bid_id=bid3.id,
            )
        )
        session.add(
            Message(
                conversation_id=conv3.id,
                actor_type=ActorType.USER,
                sender_id=users["bob@example.com"].id,
                body="Bid accepted",
                bid_id=bid3.id,
            )
        )

        switch.status = ListingStatus.SOLD

        txn2 = Transaction(
            bid_id=bid3.id,
            buyer_id=users["buyer-agent@moltplaats.nl"].id,
            seller_id=users["bob@example.com"].id,
            amount=260_00,
            status=TransactionStatus.ESCROWED,
            escrowed_at=datetime.now(UTC) - timedelta(hours=6),
        )
        session.add(txn2)

        # Adjust buyer agent wallet for escrow
        buyer_agent_wallet = await session.execute(
            select(Wallet).where(
                Wallet.user_id == users["buyer-agent@moltplaats.nl"].id
            )
        )
        ba_wallet = buyer_agent_wallet.scalar_one()
        ba_wallet.balance -= 260_00
        ba_wallet.held_balance += 260_00

        # Alice bids on Bob's Aeron chair — rejected
        aeron = next(l for l in active if "Aeron" in l.title)
        bid4 = Bid(
            listing_id=aeron.id,
            bidder_id=users["alice@example.com"].id,
            amount=350_00,
            bid_type=BidType.BUYER,
            status=BidStatus.REJECTED,
        )
        session.add(bid4)
        await session.flush()

        conv4 = Conversation(
            listing_id=aeron.id, buyer_id=users["alice@example.com"].id
        )
        session.add(conv4)
        await session.flush()

        for body, sender in [
            ("Hi Bob, would you take €350 for the Aeron?", "alice@example.com"),
            ("Bid placed: 35000", "alice@example.com"),
            (
                "Sorry, €350 is too low for this chair. It's worth every cent at €450.",
                "bob@example.com",
            ),
            ("Bid rejected", "bob@example.com"),
        ]:
            session.add(
                Message(
                    conversation_id=conv4.id,
                    actor_type=ActorType.USER,
                    sender_id=users[sender].id,
                    body=body,
                )
            )

        # Buyer Agent bids on Charlie's mountain bike — pending
        bike = next(l for l in active if "Mountain Bike" in l.title)
        bid5 = Bid(
            listing_id=bike.id,
            bidder_id=users["buyer-agent@moltplaats.nl"].id,
            amount=550_00,
            bid_type=BidType.BUYER,
            status=BidStatus.PENDING,
        )
        session.add(bid5)
        await session.flush()

        conv5 = Conversation(
            listing_id=bike.id, buyer_id=users["buyer-agent@moltplaats.nl"].id
        )
        session.add(conv5)
        await session.flush()

        session.add(
            Message(
                conversation_id=conv5.id,
                actor_type=ActorType.USER,
                sender_id=users["buyer-agent@moltplaats.nl"].id,
                body="Great bike! Would you consider €550?",
            )
        )
        session.add(
            Message(
                conversation_id=conv5.id,
                actor_type=ActorType.USER,
                sender_id=users["buyer-agent@moltplaats.nl"].id,
                body="Bid placed: 55000",
                bid_id=bid5.id,
            )
        )

        await session.flush()
        await session.commit()

        print()
        print("=== Seed complete ===")
        print()
        print("Agent accounts (password: Test1234!):")
        print(
            f"  Buyer Agent:  buyer-agent@moltplaats.nl  (id: {users['buyer-agent@moltplaats.nl'].id})"
        )
        print(
            f"  Seller Agent: seller-agent@moltplaats.nl (id: {users['seller-agent@moltplaats.nl'].id})"
        )
        print()
        print("Regular accounts (password: Test1234!):")
        print(f"  Alice:   alice@example.com   (id: {users['alice@example.com'].id})")
        print(f"  Bob:     bob@example.com     (id: {users['bob@example.com'].id})")
        print(f"  Charlie: charlie@example.com (id: {users['charlie@example.com'].id})")
        print()
        print("Scenarios seeded:")
        print(
            "  - Active negotiation with counter-offer (Buyer Agent ↔ Alice, leather jacket)"
        )
        print("  - Accepted bid, pending escrow (Bob → Seller Agent, iPhone)")
        print("  - Accepted bid, escrowed (Buyer Agent → Bob, Switch)")
        print("  - Rejected bid (Alice → Bob, Aeron chair)")
        print("  - Pending bid (Buyer Agent → Charlie, mountain bike)")


if __name__ == "__main__":
    asyncio.run(seed())
