<?php
/**
 * Kafelek wpisu na listach.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<article id="post-<?php the_ID(); ?>" <?php post_class( 'post-card' ); ?>>

	<?php if ( has_post_thumbnail() ) : ?>
		<a class="post-card__thumb" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
			<?php the_post_thumbnail( 'printarium-card', array( 'loading' => 'lazy' ) ); ?>
		</a>
	<?php endif; ?>

	<div class="post-card__body">
		<p class="post-card__meta"><?php echo esc_html( get_the_date() ); ?></p>
		<h2 class="post-card__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
		<p class="post-card__excerpt"><?php echo esc_html( wp_trim_words( get_the_excerpt(), 22 ) ); ?></p>
		<p class="mb-0 mt-3"><a class="btn btn--ghost btn--sm" href="<?php the_permalink(); ?>"><?php esc_html_e( 'Czytaj dalej', 'printarium' ); ?></a></p>
	</div>

</article>
