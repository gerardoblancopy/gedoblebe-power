function [baseMVA, bus, gen, branch] = case3_debug
%CASE3_DEBUG  3-bus debug case for LMP investigation.

baseMVA = 100;

%% bus data
%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin
bus = [
	1	3	50	0	0	0	1	1	0	230	1	1.1	0.9;
	2	1	60	0	0	0	1	1	0	230	1	1.1	0.9;
	3	1	300	0	0	0	1	1	0	230	1	1.1	0.9;
];

%% generator data
%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin
gen = [
	1	260	0	100	-100	1	100	1	310	0;
	2	90	0	100	-100	1	100	1	90	0;
	3	10	0	100	-100	1	100	1	100	0;  % Pmin=0 here
];

%% branch data
%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status
branch = [
	1	2	0.01	0.05	0	250	250	250	0	0	1;
	1	3	0.01	0.05	0	250	250	250	0	0	1;
	2	3	0.01	0.05	0	250	250	250	0	0	1;
];

%% generator cost data
%	2	startup	shutdown	n	c(n-1)	...	c0
mpc.gencost = [
	2	0	0	3	0	7	0;  % Gen 1 cost 7
	2	0	0	3	0	6	0;  % Gen 2 cost 6
	2	0	0	3	0	10	0;  % Gen 3 cost 10
];

return;
