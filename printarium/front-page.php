<?php
/**
 * Strona główna – układ zgodny z layoutem Printarium.
 *
 * Jeżeli w „Ustawienia → Czytanie” wskazano statyczną stronę początkową
 * z własną treścią, sekcje motywu wyświetlają się nad tą treścią.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="site-main">

	<?php
	get_template_part( 'template-parts/home/hero' );
	get_template_part( 'template-parts/home/categories' );
	get_template_part( 'template-parts/home/usp' );
	get_template_part( 'template-parts/home/highlights' );
	get_template_part( 'template-parts/home/products' );
	get_template_part( 'template-parts/home/faq' );
	?>

	<?php
	// Treść przypisanej strony startowej (jeśli została uzupełniona).
	if ( have_posts() ) :
		while ( have_posts() ) :
			the_post();

			$printarium_content = trim( get_the_content() );

			if ( $printarium_content ) :
				?>
				<section class="section">
					<div class="container container--narrow entry-content">
						<?php the_content(); ?>
					</div>
				</section>
				<?php
			endif;
		endwhile;
	endif;
	?>

</main>

<?php
get_footer();
