<?php
/**
 * Wyniki wyszukiwania.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();

printarium_page_hero(
	array(
		'title'    => sprintf(
			/* translators: %s: fraza wyszukiwania. */
			esc_html__( 'Wyniki dla: %s', 'printarium' ),
			esc_html( get_search_query() )
		),
		'subtitle' => sprintf(
			/* translators: %d: liczba wyników. */
			esc_html( _n( 'Znaleziono %d wynik.', 'Znaleziono %d wyników.', (int) $GLOBALS['wp_query']->found_posts, 'printarium' ) ),
			(int) $GLOBALS['wp_query']->found_posts
		),
	)
);
?>

<main id="primary" class="site-main">
	<div class="container">

		<?php if ( have_posts() ) : ?>
			<div class="grid grid--3">
				<?php
				while ( have_posts() ) :
					the_post();
					get_template_part( 'template-parts/content', 'card' );
				endwhile;
				?>
			</div>

			<?php printarium_pagination(); ?>
		<?php else : ?>
			<?php get_template_part( 'template-parts/content', 'none' ); ?>
		<?php endif; ?>

	</div>
</main>

<?php
get_footer();
