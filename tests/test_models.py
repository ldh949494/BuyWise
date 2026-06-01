from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, JSON, Numeric, String, Text

from app.core.database import Base
from app.models import (
    ChatMessage,
    ChatSession,
    Order,
    OrderItem,
    OtpChallenge,
    PriceHistory,
    Product,
    Recommendation,
    Review,
    User,
    UserSession,
)


def column(model: type[Base], name: str):
    return model.__table__.columns[name]


def index_columns(model: type[Base]) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in index.columns)
        for index in model.__table__.indexes
    }


def test_product_table_schema() -> None:
    assert Product.__tablename__ == "products"
    assert isinstance(column(Product, "id").type, BigInteger)
    assert column(Product, "id").primary_key is True
    assert column(Product, "id").autoincrement is True
    assert isinstance(column(Product, "name").type, String)
    assert column(Product, "name").type.length == 255
    assert column(Product, "name").nullable is False
    assert isinstance(column(Product, "sku").type, String)
    assert column(Product, "sku").type.length == 128
    assert isinstance(column(Product, "price").type, Numeric)
    assert column(Product, "price").type.precision == 10
    assert column(Product, "price").type.scale == 2
    assert isinstance(column(Product, "product_url").type, String)
    assert isinstance(column(Product, "image_urls").type, JSON)
    assert isinstance(column(Product, "stock_status").type, String)
    assert isinstance(column(Product, "review_summary").type, Text)
    assert isinstance(column(Product, "description").type, Text)
    assert isinstance(column(Product, "specs").type, JSON)
    assert isinstance(column(Product, "tags").type, JSON)
    assert isinstance(column(Product, "suitable_scene").type, JSON)
    assert isinstance(column(Product, "created_at").type, DateTime)
    assert ("category",) in index_columns(Product)
    assert ("price",) in index_columns(Product)


def test_review_table_schema() -> None:
    assert Review.__tablename__ == "reviews"
    assert isinstance(column(Review, "id").type, BigInteger)
    assert isinstance(column(Review, "product_id").type, BigInteger)
    assert isinstance(column(Review, "order_item_id").type, BigInteger)
    assert isinstance(column(Review, "user_ref").type, String)
    assert isinstance(column(Review, "user_name").type, String)
    assert column(Review, "user_name").type.length == 64
    assert isinstance(column(Review, "rating").type, Numeric)
    assert isinstance(column(Review, "content").type, Text)
    assert isinstance(column(Review, "sentiment").type, String)
    assert isinstance(column(Review, "source").type, String)
    assert isinstance(column(Review, "purchase_evidence").type, String)
    assert isinstance(column(Review, "pros_tags").type, JSON)
    assert isinstance(column(Review, "cons_tags").type, JSON)
    assert isinstance(column(Review, "status").type, String)
    assert isinstance(column(Review, "submitted_at").type, DateTime)
    assert isinstance(column(Review, "updated_at").type, DateTime)
    assert isinstance(column(Review, "created_at").type, DateTime)
    assert ("product_id",) in index_columns(Review)
    assert ("order_item_id",) in index_columns(Review)
    assert ("purchase_evidence",) in index_columns(Review)
    assert ("source",) in index_columns(Review)
    assert ("user_ref",) in index_columns(Review)


def test_order_table_schema() -> None:
    assert Order.__tablename__ == "orders"
    assert isinstance(column(Order, "id").type, BigInteger)
    assert isinstance(column(Order, "user_ref").type, String)
    assert column(Order, "user_ref").nullable is False
    assert isinstance(column(Order, "payment_status").type, String)
    assert isinstance(column(Order, "fulfillment_status").type, String)
    assert isinstance(column(Order, "external_platform").type, String)
    assert isinstance(column(Order, "external_order_ref").type, String)
    assert isinstance(column(Order, "paid_at").type, DateTime)
    assert isinstance(column(Order, "shipped_at").type, DateTime)
    assert isinstance(column(Order, "delivered_at").type, DateTime)
    assert ("user_ref",) in index_columns(Order)


def test_order_item_table_schema() -> None:
    assert OrderItem.__tablename__ == "order_items"
    assert isinstance(column(OrderItem, "id").type, BigInteger)
    assert isinstance(column(OrderItem, "order_id").type, BigInteger)
    assert isinstance(column(OrderItem, "product_id").type, BigInteger)
    assert isinstance(column(OrderItem, "quantity").type, Integer)
    assert isinstance(column(OrderItem, "unit_price_snapshot").type, Numeric)
    assert isinstance(column(OrderItem, "name_snapshot").type, String)
    assert isinstance(column(OrderItem, "platform_snapshot").type, String)
    assert isinstance(column(OrderItem, "product_url_snapshot").type, String)
    assert isinstance(column(OrderItem, "feedback_due_at").type, DateTime)
    assert isinstance(column(OrderItem, "feedback_submitted_at").type, DateTime)
    assert isinstance(column(OrderItem, "feedback_prompt_dismissed_at").type, DateTime)
    assert ("order_id",) in index_columns(OrderItem)
    assert ("product_id",) in index_columns(OrderItem)
    assert ("feedback_due_at",) in index_columns(OrderItem)


def test_price_history_table_schema() -> None:
    assert PriceHistory.__tablename__ == "price_history"
    assert isinstance(column(PriceHistory, "id").type, BigInteger)
    assert isinstance(column(PriceHistory, "product_id").type, BigInteger)
    assert isinstance(column(PriceHistory, "date").type, Date)
    assert isinstance(column(PriceHistory, "price").type, Numeric)
    assert ("product_id",) in index_columns(PriceHistory)
    assert ("date",) in index_columns(PriceHistory)


def test_chat_session_table_schema() -> None:
    assert ChatSession.__tablename__ == "chat_sessions"
    assert isinstance(column(ChatSession, "id").type, BigInteger)
    assert isinstance(column(ChatSession, "session_id").type, String)
    assert column(ChatSession, "session_id").type.length == 64
    assert column(ChatSession, "user_id").nullable is True
    assert isinstance(column(ChatSession, "title").type, String)
    assert isinstance(column(ChatSession, "created_at").type, DateTime)
    assert ("session_id",) in index_columns(ChatSession)


def test_user_auth_table_schemas() -> None:
    assert User.__tablename__ == "users"
    assert isinstance(column(User, "phone_e164").type, String)
    assert column(User, "phone_e164").nullable is False
    assert isinstance(column(User, "status").type, String)
    assert isinstance(column(User, "created_at").type, DateTime)
    assert ("phone_e164",) in index_columns(User)

    assert OtpChallenge.__tablename__ == "otp_challenges"
    assert isinstance(column(OtpChallenge, "code_hash").type, String)
    assert isinstance(column(OtpChallenge, "attempt_count").type, Integer)
    assert isinstance(column(OtpChallenge, "expires_at").type, DateTime)

    assert UserSession.__tablename__ == "user_sessions"
    assert isinstance(column(UserSession, "refresh_token_hash").type, String)
    assert isinstance(column(UserSession, "expires_at").type, DateTime)
    assert ("refresh_token_hash",) in index_columns(UserSession)


def test_chat_message_table_schema() -> None:
    assert ChatMessage.__tablename__ == "chat_messages"
    assert isinstance(column(ChatMessage, "id").type, BigInteger)
    assert isinstance(column(ChatMessage, "session_id").type, String)
    assert isinstance(column(ChatMessage, "role").type, String)
    assert isinstance(column(ChatMessage, "content").type, Text)
    assert isinstance(column(ChatMessage, "structured_data").type, JSON)
    assert isinstance(column(ChatMessage, "created_at").type, DateTime)
    assert ("session_id",) in index_columns(ChatMessage)


def test_recommendation_table_schema() -> None:
    assert Recommendation.__tablename__ == "recommendations"
    assert isinstance(column(Recommendation, "id").type, BigInteger)
    assert isinstance(column(Recommendation, "session_id").type, String)
    assert isinstance(column(Recommendation, "product_id").type, BigInteger)
    assert isinstance(column(Recommendation, "reason").type, Text)
    assert isinstance(column(Recommendation, "score").type, Numeric)
    assert column(Recommendation, "score").type.precision == 5
    assert column(Recommendation, "score").type.scale == 2
    assert isinstance(column(Recommendation, "explanation").type, JSON)
    assert isinstance(column(Recommendation, "created_at").type, DateTime)
    assert ("session_id",) in index_columns(Recommendation)
    assert ("product_id",) in index_columns(Recommendation)


def test_models_can_be_instantiated() -> None:
    product = Product(name="Phone", price=Decimal("1999.00"), tags=["mobile"])
    message = ChatMessage(session_id="s1", role="user", content="hello")

    assert product.name == "Phone"
    assert message.session_id == "s1"
