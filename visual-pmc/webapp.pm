dtmc

const double y1;
const double y2;
const double x1;
const double x2;
const double w1;
const double z1;
const double z2;
const double k1;

module M1

s : [1..10] init 1;

[] s=1 -> y1:(s'=2) + y2:(s'=4) + 1-y1-y2:(s'=8);
[] s=2 -> 0.20:(s'=2) + 0.55:(s'=3) + 0.25:(s'=9);
[] s=3 -> 0.7:(s'=6) + 0.3:(s'=9);
[] s=4 -> x1:(s'=10) + x2:(s'=9)+ 1-x1-x2:(s'=5);
[] s=5 -> w1:(s'=9) + 1-w1:(s'=10);
[] s=6 -> z1:(s'=7) + z2:(s'=10) + 1-z1-z2:(s'=9);
[] s=7 -> k1:(s'=9) + 1-k1:(s'=10);
[] s=8 -> 1:(s'=8);
[] s=9 -> 1:(s'=9);
[] s=10 -> 1:(s'=10);

endmodule
