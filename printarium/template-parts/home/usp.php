<?php
/**
 * Pasek atutów pod kaflami kategorii.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

$printarium_usps = array(
	array( 'icon' => 'poland', 'text' => printarium_option( 'printarium_usp_1' ) ),
	array( 'icon' => 'box', 'text' => printarium_option( 'printarium_usp_2' ) ),
	array( 'icon' => 'pencil', 'text' => printarium_option( 'printarium_usp_3' ) ),
	array( 'icon' => 'paw', 'text' => printarium_option( 'printarium_usp_4' ) ),
);
?>
<section class="section section--tight" style="padding-top:0">
	<div class="container">
		<div class="usp-bar">
			<?php foreach ( $printarium_usps as $printarium_usp ) : ?>
				<?php if ( ! $printarium_usp['text'] ) { continue; } ?>
				<div class="usp-bar__item">
					<?php printarium_icon( $printarium_usp['icon'], 28 ); ?>
					<span class="usp-bar__label"><?php echo esc_html( $printarium_usp['text'] ); ?></span>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
