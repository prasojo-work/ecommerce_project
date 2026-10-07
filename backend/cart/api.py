from __future__ import annotations

from typing import Any

from ninja import Router, Status
from ninja.errors import HttpError

from accounts.auth import jwt_auth
from cart.models import Cart, CartItem
from cart.schemas import CartItemIn, CartItemOut, CartItemPatch, CartOut
from catalog.models import ProductVariant

router = Router(tags=["cart"])


def _get_cart(user: Any) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _cart_out(cart: Cart) -> CartOut:
    rows = cart.items.select_related("variant__product").prefetch_related(
        "variant__product__images"
    )
    items: list[CartItemOut] = []
    subtotal = 0
    for row in rows:
        product = row.variant.product
        image = next(iter(product.images.all()), None)
        items.append(
            CartItemOut(
                id=row.id,
                variant_id=row.variant_id,
                product_title=product.title,
                product_slug=product.slug,
                variant_name=row.variant.name,
                image=image.url if image else None,
                unit_price=row.unit_price_snapshot,
                quantity=row.quantity,
                line_total=row.line_total,
            )
        )
        subtotal += row.line_total
    return CartOut(items=items, subtotal=subtotal, currency="IDR")


@router.get("/cart", auth=jwt_auth, response=CartOut)
def get_cart(request: Any) -> CartOut:
    return _cart_out(_get_cart(request.auth))


@router.post("/cart/items", auth=jwt_auth, response={201: CartOut})
def add_cart_item(request: Any, payload: CartItemIn) -> Status[CartOut]:
    if payload.quantity < 1:
        raise HttpError(400, "Quantity must be at least 1.")
    variant = ProductVariant.objects.filter(pk=payload.variant_id, is_active=True).first()
    if variant is None:
        raise HttpError(404, "Product variant not found.")
    cart = _get_cart(request.auth)
    item = cart.items.filter(variant=variant).first()
    if item is None:
        CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=payload.quantity,
            unit_price_snapshot=variant.effective_price,
        )
    else:
        item.quantity += payload.quantity
        item.save(update_fields=["quantity", "updated_at"])
    return Status(201, _cart_out(cart))


@router.patch("/cart/items/{item_id}", auth=jwt_auth, response=CartOut)
def update_cart_item(request: Any, item_id: int, payload: CartItemPatch) -> CartOut:
    cart = _get_cart(request.auth)
    item = cart.items.filter(pk=item_id).first()
    if item is None:
        raise HttpError(404, "Cart item not found.")
    if payload.quantity < 1:
        item.delete()
    else:
        item.quantity = payload.quantity
        item.save(update_fields=["quantity", "updated_at"])
    return _cart_out(cart)


@router.delete("/cart/items/{item_id}", auth=jwt_auth, response=CartOut)
def remove_cart_item(request: Any, item_id: int) -> CartOut:
    cart = _get_cart(request.auth)
    cart.items.filter(pk=item_id).delete()
    return _cart_out(cart)
