from __future__ import annotations

from typing import Any
from uuid import uuid4

from ninja import Query, Router, Status
from ninja.errors import HttpError

from accounts.auth import jwt_auth
from accounts.models import Address
from cart.models import Cart
from orders.models import Order, OrderItem
from orders.schemas import (
    OrderCreateIn,
    OrderFilters,
    OrderItemOut,
    OrderOut,
    OrderSummaryOut,
    PaginatedOrders,
    ShippingOptionOut,
    ShippingOptionsOut,
)
from orders.services import (
    EmptyCartError,
    InsufficientStockError,
    UnknownShippingMethodError,
    create_order_from_cart,
)
from orders.shipping import FREE_SHIPPING_THRESHOLD, options_for

router = Router(tags=["orders"])


def _cart_subtotal(user: Any) -> int:
    cart = Cart.objects.filter(user=user).first()
    if cart is None:
        return 0
    return sum(row.line_total for row in cart.items.all())


def _order_item_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        id=item.id,
        variant_id=item.variant_id,
        product_title=item.product_title_snapshot,
        variant_name=item.variant_name_snapshot,
        unit_price=item.unit_price,
        quantity=item.quantity,
        line_total=item.line_total,
    )


def _order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        number=order.number,
        status=order.status,
        subtotal=order.subtotal,
        shipping_cost=order.shipping_cost,
        total=order.total,
        currency=order.currency,
        shipping_method=order.shipping_method,
        shipping_method_name=order.shipping_method_name,
        shipping_address=order.shipping_address_snapshot,
        items=[_order_item_out(item) for item in order.items.all()],
        created_at=order.created_at,
    )


@router.get("/shipping/options", auth=jwt_auth, response=ShippingOptionsOut)
def list_shipping_options(request: Any) -> ShippingOptionsOut:
    """Options with cost + ETA, priced against the live cart (US-5.2)."""
    subtotal = _cart_subtotal(request.auth)
    return ShippingOptionsOut(
        subtotal=subtotal,
        currency="IDR",
        free_shipping_threshold=FREE_SHIPPING_THRESHOLD,
        options=[
            ShippingOptionOut(code=option.code, name=option.name, cost=cost, eta=option.eta)
            for option, cost in options_for(subtotal)
        ],
    )


@router.post("/orders", auth=jwt_auth, response={200: OrderOut, 201: OrderOut})
def create_order(request: Any, payload: OrderCreateIn) -> Status[OrderOut]:
    address = Address.objects.filter(pk=payload.address_id, user=request.auth).first()
    if address is None:
        raise HttpError(404, "Address not found.")
    try:
        order, created = create_order_from_cart(
            user=request.auth,
            address=address,
            shipping_code=payload.shipping_method,
            idempotency_key=payload.idempotency_key or uuid4().hex,
        )
    except EmptyCartError:
        raise HttpError(400, "Your cart is empty.") from None
    except UnknownShippingMethodError:
        raise HttpError(400, "Unknown shipping method.") from None
    except InsufficientStockError as exc:
        raise HttpError(409, str(exc)) from None
    return Status(201 if created else 200, _order_out(order))


@router.get("/orders", auth=jwt_auth, response=PaginatedOrders)
def list_orders(request: Any, filters: Query[OrderFilters]) -> PaginatedOrders:
    queryset = Order.objects.filter(user=request.auth).order_by("-created_at", "-id")
    total = queryset.count()
    page = max(filters.page, 1)
    page_size = min(max(filters.page_size, 1), 100)
    offset = (page - 1) * page_size
    page_items = queryset.prefetch_related("items")[offset : offset + page_size]
    return PaginatedOrders(
        count=total,
        page=page,
        page_size=page_size,
        results=[
            OrderSummaryOut(
                id=order.id,
                number=order.number,
                status=order.status,
                total=order.total,
                currency=order.currency,
                item_count=sum(item.quantity for item in order.items.all()),
                created_at=order.created_at,
            )
            for order in page_items
        ],
    )


@router.get("/orders/{number}", auth=jwt_auth, response=OrderOut)
def order_detail(request: Any, number: str) -> OrderOut:
    order = (
        Order.objects.filter(user=request.auth, number=number).prefetch_related("items").first()
    )
    if order is None:
        raise HttpError(404, "Order not found.")
    return _order_out(order)
