<?php
/**
 * Sekcja hero na stronie głównej.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_hero_image = printarium_option( 'printarium_hero_image' );
$printarium_btn1_label = printarium_option( 'printarium_hero_btn1_label' );
$printarium_btn1_url   = printarium_option( 'printarium_hero_btn1_url' );
$printarium_btn2_label = printarium_option( 'printarium_hero_btn2_label' );
$printarium_btn2_url   = printarium_option( 'printarium_hero_btn2_url' );
?>
<section class="hero">

	<?php if ( $printarium_hero_image ) : ?>
		<div class="hero__media">
			<?php echo wp_get_attachment_image( (int) $printarium_hero_image, 'printarium-hero', false, array( 'alt' => '', 'fetchpriority' => 'high' ) ); ?>
		</div>
	<?php endif; ?>

	<div class="container">
		<div class="hero__inner">
			<h1 class="hero__title"><?php echo wp_kses_post( printarium_option( 'printarium_hero_title' ) ); ?></h1>
			<p class="hero__text"><?php echo wp_kses_post( printarium_option( 'printarium_hero_text' ) ); ?></p>

			<div class="hero__actions">
				<?php if ( $printarium_btn1_label ) : ?>
					<a class="btn btn--primary" href="<?php echo esc_url( $printarium_btn1_url ); ?>"><?php echo esc_html( $printarium_btn1_label ); ?></a>
				<?php endif; ?>

				<?php if ( $printarium_btn2_label ) : ?>
					<a class="btn btn--secondary" href="<?php echo esc_url( $printarium_btn2_url ); ?>"><?php echo esc_html( $printarium_btn2_label ); ?></a>
				<?php endif; ?>
			</div>
		</div>
	</div>

</section>
