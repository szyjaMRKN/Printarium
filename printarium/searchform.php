<?php
/**
 * Formularz wyszukiwania.
 *
 * Na stronach sklepu szuka w produktach, poza sklepem – w całej witrynie.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_search_id = 'search-' . wp_unique_id();
$printarium_is_shop   = printarium_is_woocommerce_active() && ( is_woocommerce() || is_cart() || is_checkout() );
?>
<form role="search" method="get" class="search-form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
	<label class="screen-reader-text" for="<?php echo esc_attr( $printarium_search_id ); ?>">
		<?php echo $printarium_is_shop ? esc_html__( 'Szukaj produktów', 'printarium' ) : esc_html__( 'Szukaj', 'printarium' ); ?>
	</label>

	<span class="search-field-wrap" style="flex:1">
		<input
			type="search"
			id="<?php echo esc_attr( $printarium_search_id ); ?>"
			class="search-field"
			name="s"
			value="<?php echo esc_attr( get_search_query() ); ?>"
			placeholder="<?php echo $printarium_is_shop ? esc_attr__( 'Szukaj produktów…', 'printarium' ) : esc_attr__( 'Czego szukasz?', 'printarium' ); ?>"
		>
		<span class="search-field-wrap__icon"><?php printarium_icon( 'search', 20 ); ?></span>
	</span>

	<?php if ( $printarium_is_shop ) : ?>
		<input type="hidden" name="post_type" value="product">
	<?php endif; ?>

	<button type="submit" class="btn btn--primary search-submit"><?php esc_html_e( 'Szukaj', 'printarium' ); ?></button>
</form>
