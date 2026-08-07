<?php
/**
 * Sidebar sklepu (wywoływany przez WooCommerce, gdy motyw go użyje).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

if ( ! is_active_sidebar( 'shop-sidebar' ) ) {
	return;
}
?>
<aside class="shop-sidebar" id="shop-filters">
	<div class="shop-sidebar__inner">
		<?php dynamic_sidebar( 'shop-sidebar' ); ?>
	</div>
</aside>
