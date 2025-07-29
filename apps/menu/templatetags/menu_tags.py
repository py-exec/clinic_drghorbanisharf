# apps/menu/templatetags/menu_tags.py

import logging
from apps.menu.models import MenuItem
# Import build_menu_tree and get_menu_version from utils
from apps.menu.utils import build_menu_tree, get_menu_version
from django import template
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

register = template.Library()


@register.inclusion_tag("partials/_menu_tree.html", takes_context=True)
def render_dynamic_menu(context, request=None):
    """
    Inclusion tag for rendering the dynamic menu.
    This tag fetches menu data from cache or rebuilds and caches it.
    The `request` object is either passed explicitly or retrieved from the template context.
    """
    # Use the explicitly passed request if available, otherwise try to get it from context.
    current_request = request if request is not None else context.get("request")

    if not current_request:
        # Log an error if the request object is missing, which indicates a misconfiguration.
        logger.error("Request object is missing in template context for render_dynamic_menu. Returning empty menu.")
        return {"menu_tree": []}

    user = current_request.user

    # Get the current menu version for cache key invalidation.
    menu_version = get_menu_version()

    # Determine the cache key based on user authentication status and menu version.
    cache_key = f"dynamic_menu_user_{user.id if user.is_authenticated else 'guest'}_v{menu_version}"

    # Get the cache timeout from settings.py or use a default value.
    menu_cache_timeout = getattr(settings, "MENU_CACHE_TIMEOUT", 3600)

    # Attempt to retrieve the menu tree from cache.
    # menu_tree = cache.get(cache_key)
    menu_tree = None

    # If the menu tree is not found in cache, build it.
    if not menu_tree:
        # Fetch all active and visible menu items from the database.
        # select_related and prefetch_related are used for query optimization.
        all_items = list(
            MenuItem.objects.select_related("parent").prefetch_related("permissions", "required_roles").filter(
                is_active=True, show_in_menu=True
            ).order_by("order")
        )

        # Build the hierarchical menu tree using the build_menu_tree utility function.
        # The current_request is passed to enable smart highlighting based on the active URL.
        menu_tree = build_menu_tree(all_items, user, current_request)

        # Cache the built menu tree.
        cache.set(cache_key, menu_tree, menu_cache_timeout)
    # Return the menu tree to the template.
    return {"menu_tree": menu_tree}


@register.inclusion_tag("partials/_sub_menu.html", takes_context=True)
def render_sub_menu(context, children):
    request = context.get("request")

    return {"children": children, "request": request}
