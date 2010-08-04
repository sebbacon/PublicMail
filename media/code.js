$(document).ready(function() {
  $('div.email div.header').hover(
    function() {
      $('div.anchor a').toggleClass('visible');
    }
   ).click(
    function() {
      $('div.headers div.extra').toggle('slow');
    }
  );
  $('div.message div.uncollapse').toggle(
    function() {
	$(this).next().toggle();
	$(this).text("- hide quoted text -")
    },
    function() {
	$(this).next().toggle();
	$(this).text("- show quoted text -")
    });
});

