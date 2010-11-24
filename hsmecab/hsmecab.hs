{-# LANGUAGE OverloadedStrings, ViewPatterns #-}
import Control.Monad
import Data.List
import qualified Data.Text as T
import qualified Data.Text.IO as TIO
import qualified Data.Text.ICU.Convert as TConv
import qualified Data.ByteString as B
import qualified Data.Map as M
import System.IO
import System.Process

runMecab args = runInteractiveProcess "mecab" args Nothing Nothing
toMecab txt = TConv.open "EUC-JP" Nothing >>= return . flip TConv.fromUnicode txt
fromMecab bs = TConv.open "EUC-JP" Nothing >>= return . flip TConv.toUnicode bs
useMecab p@(inp,out,err,pid) txt = do
   hSetBuffering inp LineBuffering
   toMecab txt >>= B.hPutStrLn inp
   os <- replicateM n (B.hGetLine out >>= fromMecab)
   return $ T.intercalate "\n" os
   where n = 1 + T.count "\n" txt

morphRun = runMecab ["--node-format=%m\t%f[0]\t%f[1]\t%f[8]$NODESTOP$", "--eos-format=\n", "--unk-format=%m\tUnknown\tUnknown\tUnknown$NODESTOP$"]
printDb = mapM_ TIO.putStrLn . map (T.intercalate (T.pack "\t")) . M.elems

morphs = do
   m <- morphRun
   o <- useMecab m "好き\nです\n時は来た"
   let os = nub $ init $ T.split "$NODESTOP$" $ T.replace "\n" "" o
   let ms = map (T.split (T.pack "\t")) os
   let db = M.fromList $ zip (map head ms) ms
   return db

main = morphs >>= putStrLn . show
