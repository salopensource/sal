(function () { 'use strict';

$( document ).ready( function() {
  $( '#id_munki_item' ).select2({
    placeholder: "select software",
  });

  $( '#id_search_field' ).select2({
    placeholder: "search field",
  });
});

}()); // end 'use strict'
