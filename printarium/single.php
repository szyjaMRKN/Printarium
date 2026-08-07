<?php
/**
 * Pojedynczy wpis.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();

while ( have_posts() ) :
	the_post();

	printarium_page_hero(
		array(
			'title'    => get_the_title(),
			'subtitle' => sprintf(
				/* translators: 1: data publikacji, 2: autor. */
				esc_html__( '%1$s · %2$s', 'printarium' ),
				esc_html( get_the_date() ),
				esc_html( get_the_author() )
			),
		)
	);
	?>

	<main id="primary" class="site-main">
		<div class="container container--narrow">

			<?php if ( has_post_thumbnail() ) : ?>
				<figure class="mb-3">
					<?php the_post_thumbnail( 'printarium-hero', array( 'style' => 'border-radius:var(--pr-radius)' ) ); ?>
				</figure>
			<?php endif; ?>

			<article id="post-<?php the_ID(); ?>" <?php post_class( 'entry-content' ); ?>>
				<?php the_content(); ?>
			</article>

			<?php
			$printarium_tags = get_the_tag_list( '<div class="product-card__chips mt-3">', '', '</div>' );
			if ( $printarium_tags ) {
				echo wp_kses_post( $printarium_tags );
			}
			?>

			<nav class="pagination" aria-label="<?php esc_attr_e( 'Nawigacja między wpisami', 'printarium' ); ?>">
				<ul class="pagination__list">
					<?php
					$printarium_prev = get_previous_post();
					$printarium_next = get_next_post();

					if ( $printarium_prev ) {
						echo '<li class="pagination__item"><a class="page-numbers" href="' . esc_url( get_permalink( $printarium_prev ) ) . '">' . esc_html__( '← Poprzedni', 'printarium' ) . '</a></li>';
					}
					if ( $printarium_next ) {
						echo '<li class="pagination__item"><a class="page-numbers" href="' . esc_url( get_permalink( $printarium_next ) ) . '">' . esc_html__( 'Następny →', 'printarium' ) . '</a></li>';
					}
					?>
				</ul>
			</nav>

			<?php
			if ( comments_open() || get_comments_number() ) {
				comments_template();
			}
			?>

		</div>
	</main>

	<?php
endwhile;

get_footer();
