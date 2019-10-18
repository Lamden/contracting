
## Code Comparisons
Observe some of these examples of other smart contracting languages and comparable Contracting code. Which one would you rather use?

## Multisig
A multisignature contract is one where two or more parties control a single account. Both parties need to sign off for a transfer to occur.

### Plutus
Plutus is a Haskell-like language for the Cardano blockchain platform.
```haskell
{-# LANGUAGE FlexibleContexts    #-}
{-# LANGUAGE DataKinds           #-}
{-# LANGUAGE DeriveGeneric       #-}
{-# LANGUAGE OverloadedStrings   #-}
{-# LANGUAGE RecordWildCards     #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE TemplateHaskell     #-}
{-# LANGUAGE NoImplicitPrelude   #-}
{-# OPTIONS_GHC -fno-ignore-interface-pragmas #-}
-- | Implements an n-out-of-m multisig contract.
module Language.PlutusTx.Coordination.Contracts.MultiSig
    ( MultiSig(..)
    , msValidator
    , validate
    , msDataScript
    , msRedeemer
    , msAddress
    , lock
    , initialise
    , unlockTx
    ) where

import qualified Data.Map                     as Map
import qualified Data.Set                     as Set
import           Language.PlutusTx.Prelude
import qualified Language.PlutusTx            as PlutusTx
import           Ledger                       as Ledger hiding (initialise, to)
import qualified Ledger.Typed.Scripts         as Scripts
import           Ledger.Validation            as V
import           Wallet.API                   as WAPI

data MultiSig = MultiSig
                { signatories :: [Ledger.PubKey]
                -- ^ List of public keys of people who may sign the transaction
                , requiredSignatures :: Integer
                -- ^ Minimum number of signatures required to unlock
                --   the output (should not exceed @length signatories@)
                }
PlutusTx.makeLift ''MultiSig

validate :: MultiSig -> () -> () -> PendingTx -> Bool
validate (MultiSig keys num) _ _ p =
    let present = length (filter (V.txSignedBy p) keys)
    in present >= num

msValidator :: MultiSig -> ValidatorScript
msValidator sig = mkValidatorScript $
    $$(PlutusTx.compile [|| validatorParam ||])
        `PlutusTx.applyCode`
            PlutusTx.liftCode sig
    where validatorParam s = Scripts.wrapValidator (validate s)

-- | Multisig data script (unit value).
msDataScript :: DataScript
msDataScript = DataScript $ PlutusTx.toData ()

-- | Multisig redeemer (unit value).
msRedeemer :: RedeemerScript
msRedeemer = RedeemerScript $ PlutusTx.toData ()

-- | The address of a 'MultiSig' contract.
msAddress :: MultiSig -> Address
msAddress = Ledger.scriptAddress . msValidator

-- | Lock some funds in a 'MultiSig' contract.
lock :: (WalletAPI m, WalletDiagnostics m) => MultiSig -> Value -> m ()
lock ms vl = payToScript_ defaultSlotRange (msAddress ms) vl msDataScript

-- | Instruct the wallet to start watching the contract address
initialise :: (WalletAPI m) => MultiSig -> m ()
initialise = startWatching . msAddress

-- | Create a transaction that unlocks the funds. It has the signature of the
--   current wallet attached.
unlockTx :: (Monad m, WalletAPI m) => MultiSig -> m Tx
unlockTx ms = do
    let
        validator = msValidator ms
        address   = msAddress ms

    utxos <- WAPI.outputsAt address

    let

        mkIn :: TxOutRef -> TxIn
        mkIn r = Ledger.scriptTxIn r validator msRedeemer

        ins = Set.map mkIn (Map.keysSet utxos)
        val = fold (Ledger.txOutValue . snd <$> Map.toList utxos)

    ownOutput <- WAPI.ownPubKeyTxOut val

    let tx = Ledger.Tx
                { txInputs = ins
                , txOutputs = [ownOutput]
                , txForge = zero
                , txFee   = zero
                , txValidRange = defaultSlotRange
                , txSignatures = Map.empty
                }

    signTxn tx
```

### Contracting

```python
import

owner_1 = Variable()
owner_2 = Variable()

@construct
def seed(o_1, o_2):
    assert ctx.caller == o_1 or ctx.caller == o_2, 'Caller cannot set another owner.'
    owner_1.set(o_1)
    owner_2.set(o_2)

@export
def transfer(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@export
def balance(account):
    return balances[account]

```