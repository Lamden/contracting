'''
how the modules import each other. this is to test ctx.caller etc

   1
 |   |
 2   3
| | | |
4 5 6 7
  |
  8

'''

import module2
import module3

print('{} called from {}, signed by {}'.format(ctx.this, ctx.caller, ctx.signer))