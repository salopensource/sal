/*
 * Author: Alex Mackey Site: simpleisbest.co.uk Description: First stab at
 * wrapper for jQuery AJAX method to retry requests
 */
(function($) {
    "use strict";
    $.ajaxWithRetries = function(options, retryConfig) {
        var retryCounter = 1;
        var originalErrorFunc = options.error, config = {
          retries : 3,
          backoff : false,
          backoffInterval : 1000,
          backOffFunc : function(currentInterval) {
              return currentInterval * 2;
          }
        };
        $.extend(config, retryConfig);
        options.error = function() {
            if (retryCounter === config.retries) {
                retryCounter = 1;
                if (typeof originalErrorFunc !== "undefined") {
                    originalErrorFunc();
                }
            } else {
                retryCounter++;
                if (config.exponentialBackoff) {
                    config.backoffInterval = retryCounter === 0 ? config.backoffInterval
                        : config.backOffFunc(config.backoffInterval);
                }
                setTimeout(function() {
                    $.ajax(options);
                }, config.backoffInterval);
            }
        };
        return $.ajax(options);
    };
})(jQuery);