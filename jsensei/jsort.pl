#!/usr/bin/perl
use Lingua::JA::Sort::JIS qw(jsort);

@in = <STDIN>;
@sorted = jsort @in;
print @sorted;
