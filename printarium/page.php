<?php
/**
 * Szablon strony.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();

while ( have_posts() ) :
	the_post();

	printarium_page_hero(
		array(
			'title' => get_the_title(),
			// Podtytuł tylko z ręcznie wpisanej zajawki – automatyczna
			// powielałaby treść strony w nagłówku.
			'subtitle' => has_excerpt() ? get_the_excerpt() : '',
		)
	);
	?>

	<main id="primary" class="site-main">
		<div class="container">
			<article id="post-<?php the_ID(); ?>" <?php post_class( 'entry-content' ); ?>>
				<?php
				the_content();

				wp_link_pages(
					array(
						'before' => '<nav class="pagination"><ul class="pagination__list"><li class="pagination__item">',
						'after'  => '</li></ul></nav>',
					)
				);
				?>
			</article>

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
