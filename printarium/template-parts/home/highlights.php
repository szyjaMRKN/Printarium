<?php
/**
 * Sekcja „Stworzone dla Twojego świata” – dwa duże kafle ze zdjęciem.
 *
 * Kafle budowane są z dwóch pierwszych kategorii sklepu; opis pochodzi
 * z opisu kategorii (Produkty → Kategorie → Opis).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_tiles = array_slice( printarium_get_shop_categories( 5 ), 0, 2 );

if ( count( $printarium_tiles ) < 2 ) {
	return;
}
?>
<section class="section">
	<div class="container">

		<?php
		printarium_section_head(
			printarium_option( 'printarium_products_title' ),
			printarium_option( 'printarium_products_text' )
		);
		?>

		<div class="highlight-grid">
			<?php foreach ( $printarium_tiles as $printarium_term ) : ?>
				<?php
				$printarium_link  = get_term_link( $printarium_term );
				$printarium_thumb = get_term_meta( $printarium_term->term_id, 'thumbnail_id', true );

				if ( is_wp_error( $printarium_link ) ) {
					continue;
				}
				?>
				<a class="highlight-tile" href="<?php echo esc_url( $printarium_link ); ?>">
					<?php if ( $printarium_thumb ) : ?>
						<div class="highlight-tile__media">
							<?php echo wp_get_attachment_image( (int) $printarium_thumb, 'printarium-tile', false, array( 'alt' => '', 'loading' => 'lazy' ) ); ?>
						</div>
					<?php endif; ?>

					<div class="highlight-tile__content">
						<h3 class="highlight-tile__title">
							<?php printarium_icon( printarium_category_icon_name( $printarium_term->slug ), 22 ); ?>
							<?php echo esc_html( $printarium_term->name ); ?>
						</h3>
						<p class="highlight-tile__text">
							<?php
							echo esc_html(
								$printarium_term->description
									? wp_trim_words( wp_strip_all_tags( $printarium_term->description ), 18 )
									: __( 'Zobacz pełną ofertę w tej kategorii.', 'printarium' )
							);
							?>
						</p>
					</div>
				</a>
			<?php endforeach; ?>
		</div>

	</div>
</section>
