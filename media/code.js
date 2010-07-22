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
});
