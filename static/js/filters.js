/*******************************************************************/
/* FILTERS */
/*******************************************************************/
(function() {
    /* got from: http://stackoverflow.com/a/18096071/1522342 */
    app.filter('cut', function() {
        return function(value, wordwise, max, tail) {
            if (!value)
                return '';

            max = parseInt(max, 10);
            if (!max)
                return value;
            if (value.length <= max)
                return value;

            value = value.substr(0, max);
            if (wordwise) {
                var lastspace = value.lastIndexOf(' ');
                if (lastspace != -1) {
                    value = value.substr(0, lastspace);
                }
            }

            return value + (tail || ' …');
        };
    });
    app.filter('brDate', function() {
        return function(value) {
            return value.split("-").reverse().join("-");
        };
    });
})();
