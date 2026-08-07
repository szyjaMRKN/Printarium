<?php
/**
 * Kafle głównych kategorii sklepu.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_categories = printarium_get_shop_categories( 5 );

if ( empty( $printarium_categories ) ) {
	return;
}
?>
<section class="section section--tight">
	<div class="container">
		<div class="category-grid">
			<?php foreach ( $printarium_categories as $printarium_term ) : ?>
				<?php
				$printarium_link = get_term_link( $printarium_term );

				if ( is_wp_error( $printarium_link ) ) {
					continue;
				}
				?>
				<a class="category-card" href="<?php echo esc_url( $printarium_link ); ?>">
					<h2 class="category-card__title"><?php echo esc_html( $printarium_term->name ); ?></h2>

					<figure class="category-card__figure">
						<?php echo printarium_category_thumbnail( $printarium_term ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					</figure>

					<span class="category-card__arrow" aria-hidden="true">
						<?php printarium_icon( 'arrow-right', 20 ); ?>
					</span>
				</a>
			<?php endforeach; ?>
		</div>
	</div>
</section>
