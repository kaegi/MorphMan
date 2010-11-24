import Control.Monad.Fix
import System
import Test.QuickCheck
import Test.QuickCheck.Modifiers

-- figure out how many total reps are needed to review rem cards assuming
-- acc accuracy
f 0 acc total = total
f rem acc total = f rem' acc total'
   where rem' = rem - succeed
         total' = total + rem
         succeed = max 1 (floor $ (fromIntegral rem) * acc)

prep_100acc :: Positive Integer -> Bool
prep_100acc n = f n 1.0 0 == n

test = do
   quickCheck prep_100acc

main = do
   args <- getArgs
   case args of
      [due,acc] -> putStrLn $ show $ f (read due) (read acc) 0
      otherwise -> putStrLn "Usage: ./app numDue accuracy.\nEx: 500 due @ 90% acc =>\n$ ./app 500 0.9\n556\n$"
