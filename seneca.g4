/*
 * PARSER
 */

// identifier of a variable
id
	: STRING

comment
	: '`'

// _my_method(text var1, decimal var2):
method_definition
	: [ '_' ] STRING 
	  '(' variable_definition 
	  { ',' variable_definition } 
	  ')' ':' NEWLINE

string_literal
	: ''' STRING '''

boolean_literal
	: 'true' 
	| 'false'

int_literal
	: NON_ZERO
	  NUMBER

float_literal
	: int_literal 
	  [ '.' NUMBER ]

uuid_literal
	: 8 * HEX '-' 
	  4 * HEX '-' 
	  4 * HEX '-' 
	  4 * HEX '-' 
	  12 * HEX

literal
	: string_literal
	| boolean_literal
	| int_literal
	| float_literal
	| uuid_literal

comparators
	: '==' 
	| '!=' 
	| '>=' 
	| '<=' 
	| '>' 
	| '<'

// bob == 15
comparison
	: (literal | id)
	  comparators
	  (literal | id)

// where
where
	: 'where' ( string_literal | id ) [ '.' id ] comparison

if_query
	: 'if' ( comparison | 'exists' )

id_tuple
	: '(' id { ',' id } ')'

// key : value
kv_pair
	:  id ':' ( literal | id )

/*
	{
		key : value,
		key : value
	}
*/
dict_query
	: '{' kv_pair { ',' kv_pair } '}'

/*
	delete user from table
	where user.name = (name)
	if user.timestamp == 12345
*/
delete_query
	: 'delete' ( string_literal | id ) 
	  'from' ( string_literal | id )
	  [ where ]
	  [ if_query ]

/* 
	insert {
		key : value,
		key : value
	} into users
*/
insert_query
	: 'insert' kv_pair
	  'into' ( string_literal | id )
	  [ where ]
	  [ if_query ]

update_query
	: 'update' kv_pair
	  'from' ( string_literal | id ) 
	  'where' kv_pair
	  [ if_query ]

/*
 * LEXER
 */

NUMBER : [0-9]+;
NON_ZERO : [1-9]
WHITESPACE : ' ' -> skip;
STRING : [a-z]+;
INDENT : '\t'
NEWLINE : '\n'
TEXT : ~[\])]+ ;
HEX : '0' 
	| '1' 
	| '2' 
	| '3' 
	| '4' 
	| '5' 
	| '6' 
	| '7' 
	| '8' 
	| '9' 
	| 'a' 
	| 'b' 
	| 'c' 
	| 'd' 
	| 'e' 
	| 'f' 
	| 'A' 
	| 'B' 
	| 'C' 
	| 'D' 
	| 'E' 
	| 'F'