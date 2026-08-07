<?php
/**
 * Pusty koszyk (sekcja 1 systemu projektowego 03).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

do_action( 'woocommerce_cart_is_empty' );
?>
<div class="cart-empty-state">
	<span class="cart-empty-state__icon"><?php printarium_icon( 'cart', 48 ); ?></span>
	<h2><?php esc_html_e( 'Twój koszyk jest pusty', 'printarium' ); ?></h2>
	<p class="text-muted mb-3"><?php esc_html_e( 'Dodaj produkty, aby kontynuować zakupy.', 'printarium' ); ?></p>

	<?php if ( wc_get_page_id( 'shop' ) > 0 ) : ?>
		<a class="btn btn--primary btn--lg" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">
			<?php esc_html_e( 'Przejdź do sklepu', 'printarium' ); ?>
		</a>
	<?php endif; ?>
</div>
