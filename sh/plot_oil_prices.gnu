set terminal png nocrop enhanced font "Arial" 9 size 640,400
set output '../images/oil_prices.png'
set style data linespoints

plot '../data/usa/oil_prices.dat' using 1:3 title column(3) lc rgb "#999999", '' using 1:4 title column(4) lc rgb "#333333"
