/*

*/

grammar toy_lang;

integer_vals
    : '#'
    | '%'
    | '&'
    | '++';

integer_index
    : '&' integer_vals;


integer_setter
    : '#' integer_setter_vals;

integer_setter_vals
    : '%'
    | '#';

integer_operation
    : integer operator integer;

operator
    : '&'
    | '+'
    | '$'
    | '-';

integer
    : '*'
    | '**'
    | '***';

output
    : '@' integer
    | '@@' integer