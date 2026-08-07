<?php
/**
 * Archiwa (kategorie, tagi, autorzy, daty).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();

printarium_page_hero(
	array(
		'title'    => get_the_archive_title(),
		'subtitle' => get_the_archive_description(),
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
