<?php
/**
 * Sekcja FAQ na stronie głównej.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<section class="section" style="padding-top:0">
	<div class="container container--narrow">
		<?php printarium_section_head( __( 'Najczęstsze pytania', 'printarium' ) ); ?>
		<?php echo do_shortcode( '[printarium_faq]' ); ?>
	</div>
</section>
