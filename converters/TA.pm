#!/usr/bin/perl -w
#
#    Copyright (C) 2012, Stuart Wolf <stuart_wolf@sourceforge.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#    02111-1307, USA
#
#
# This code derived from Padzensky's work on package Finance::YahooQuote,
# but extends its capabilites to encompas a greater number of data sources.
#
# version 1.18
# date: 2013-11-03
# author: Stuart Wolf
# - change LR_URL so that it contains the term SYMBOL which is then replaced by 
#   the actual symbol every iteration
#
# version 1.17
# date: 2012-03-26
# author: Stuart Wolf
# - initial version

require 5.005;

use strict;

package Finance::Quote::TA;

use vars qw($VERSION $LR_URL);

use LWP::UserAgent;
use HTTP::Request::Common;
use HTML::TableExtract;

$VERSION = '1.18';

#my $LR_URL = 'http://www.bizportal.co.il/shukhahon/bizcompquote.shtml?p_id=';
#my $LR_URL = 'http://www.tase.co.il/TASE/Management/GeneralPages/SimpleSearchResult.htm?objectId=&objectType=&securityType=&searchTerm=';
my $LR_URL = 'http://www.tase.co.il/eng/management/generalpages/pages/simplesearchresult.aspx?ObjectId=SYMBOL&SecurityType=0&ObjectType=1';
#my $LR_URL = 'http://www.tase.co.il/TASEEng/Management/GeneralPages/PopUpGrid.htm?tbl=0&Columns=en-US_AddColColumns&Titles=en-US_AddColTitles&ds=en-US_ds&gridName=';
#my $LR_URL = 'https://finance.bankhapoalim.co.il/cgi-bin/poalwwwc?DataRowTik=Y&reqName=action&mpux=&transactionId=ShukHoon*first&shelav=DETAILS1&PrevShelav=TIK&niarZar=&kamut=kamut&isZar=false&misparNiar=';


sub methods { return (tase => \&tase); }
{ 
	my @labels = qw/symbol name date currency method exchange last nav timezone/;

	sub labels { return (tase => \@labels); } 
}

# print out tables returned after html::TableExtract
sub debug_print {
	my ($ts, $row);
	my $te = shift(@_);
	
	print "DEBUG", "\n";
	foreach $ts ($te->tables) {
	 print "Table (", join(',', $ts->coords), "):\n";
	 foreach $row ($ts->rows) {
	  print join(', ', @$row), "\n";	  
	 }
	}
}

sub tase {
	my $quoter = shift;
	my @stocks = @_;
	my (%info,$reply,$url,$te,$ts,$row,$style);
	my $ua = $quoter->user_agent();

	# add http header so that request identified as comingfrom a browser
    $ua->agent('Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)');
	# increase default timeout to 60 seconds
	$ua->timeout(60);
	
	foreach my $stocks (@stocks)
	{
        # substitute SYMBOL with the value of 'stock' in the string LR_URL without changing LR_URL
		$url = $LR_URL =~ s/SYMBOL/$stocks/r;
#		print $url, "\n";
		$reply = $ua->request(GET $url);  

		if ($reply->is_success) 
		{
#			 print STDERR $reply->content,"\n";

			$te = new HTML::TableExtract(  headers => [qw(ISIN Symbol Price Change)] );			
#			$te = new HTML::TableExtract(  );
			$te->parse($reply->content);

#			debug_print($te);
			
			unless ( $te->tables)
			{
				$info {$stocks,"success"} = 0;
				$info {$stocks,"errormsg"} = "Stock name $stocks not found";
				next;
			}

			my @rows;
			unless (@rows = $te->rows)
			{
				$info {$stocks,"success"} = 0;
				$info {$stocks,"errormsg"} = "Parse error";
				next;
			}
		
			$info{$stocks, "success"}=1;
			$info{$stocks, "exchange"}="Tel-Aviv Stock Exchange";
			$info{$stocks, "method"}="tase";
			$info{$stocks, "symbol"}=$stocks;
			($info{$stocks, "name"}=$rows[0][0]); # ISIN
			($info{$stocks, "last"}=$rows[0][2]) =~ s/,//g;
			($info{$stocks, "last"} /= 100);
			($info{$stocks, "p_change"}=$rows[0][3]);# =~ s/\s*//g;

            $quoter->store_date(\%info, $stocks, {today => 1});

			$info{$stocks,"currency"}="ILS";
			
			# before start of trade the price is in another table (7,1)
			# this is indicated when the "last" value is 0
			if ($info{$stocks, "last"} eq '0')
			{
			    my $te = new HTML::TableExtract( depth => 7, count => 1);
				$te->parse($reply->content);
				
				unless ( $te->tables)
				{
					$info {$stocks,"success"} = 0;
					$info {$stocks,"errormsg"} = "Value for $stocks is 0";
					next;
				}				
#				debug_print($te);
				my @rows;
				unless (@rows = $te->rows)
				{
					$info {$stocks,"success"} = 0;
					$info {$stocks,"errormsg"} = "Parse error";
					next;
				}				
				
				# at last! found the row and can extract the value
				($info{$stocks, "last"}=$rows[0][1]) =~ s/,//g;
				($info{$stocks, "last"} /= 100);				
			}
		} 
		else {
     		$info{$stocks, "success"}=0;
			$info{$stocks, "errormsg"}="Error retreiving $stocks ";
   		}
 	} 
	
 	return wantarray() ? %info : \%info;
 	return \%info;
}
1;

=head1 NAME

Finance::Quote::tase Obtain quotes from http://www.tase.co.il/TASEEng

=head1 SYNOPSIS

    use Finance::Quote;

    $q = Finance::Quote->new;

    %info = Finance::Quote->fetch("tase","FR0000031122");  # Only query tase
 
=head1 DESCRIPTION

This module fetches information from the "Tel-Aviv Stock Exchange",
http://www.tase.co.il/TASEEng. All stocks are available. 
Stock symbols are their ISIN number. Hebrew is not supported.

This module is loaded by default on a Finance::Quote object. It's 
also possible to load it explicity by placing "tase" in the argument
list to Finance::Quote->new().

Using the "tase" method will guarantee that your information only comes from the Tel-Aviv Stock Exchange.
 
Information obtained by this module may be covered by http://www.tase.co.il
terms and conditions See http://www.tase.co.il for details.

=head1 LABELS RETURNED

The following labels may be returned by Finance::Quote::tase :
name, last, date, p_change, open, high, low, close, 
volume, currency, method, exchange.

=head1 SEE ALSO

Tel-Aviv, http://www.tase.co.il/TASEEng

=cut

	
