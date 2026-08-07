<?php
/**
 * Sekcja z produktami na stronie głównej (najnowsze produkty).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

if ( ! printarium_is_woocommerce_active() ) {
	return;
}

$printarium_shop_url = wc_get_page_permalink( 'shop' );
?>
<section class="section" style="padding-top:0">
	<div class="container">

		<?php printarium_section_head( __( 'Polecane produkty', 'printarium' ) ); ?>

		<?php
		echo do_shortcode( '[products limit="8" columns="4" orderby="date" order="DESC" visibility="visible"]' );
		?>

		<?php if ( $printarium_shop_url ) : ?>
			<p class="text-center mt-5 mb-0">
				<a class="btn btn--secondary btn--lg" href="<?php echo esc_url( $printarium_shop_url ); ?>">
					<?php esc_html_e( 'Zobacz wszystkie produkty', 'printarium' ); ?>
				</a>
			</p>
		<?php endif; ?>

	</div>
</section>
