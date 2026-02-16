function mpc = case9
%CASE9    Power flow data for 9 bus, 3 generator case
%   Based on Wood & Wollenberg, Example 6.3

mpc.version = '2';
mpc.baseMVA = 100;

% bus data
%    bus_i    type    Pd    Qd    Gs    Bs    area    Vm    Va    baseKV    zone    Vmax    Vmin
mpc.bus = [
    1    3    0    0    0    0    1    1    0    345    1    1.1    0.9;
    2    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    3    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    4    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    5    1    125    50    0    0    1    1    0    345    1    1.1    0.9;
    6    1    90    30    0    0    1    1    0    345    1    1.1    0.9;
    7    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    8    1    0    0    0    0    1    1    0    345    1    1.1    0.9;
    9    1    100    35    0    0    1    1    0    345    1    1.1    0.9;
];

% generator data
%    bus    Pg    Qg    Qmax    Qmin    Vg    mBase    status    Pmax    Pmin    Pc1    Pc2    Qc1min    Qc1max    Qc2min    Qc2max    ramp_agc    ramp_10    ramp_30    ramp_q    apf
mpc.gen = [
    1    0    0    300    -300    1    100    1    250    10    0    0    0    0    0    0    0    0    0    0    0;
    2    0    0    300    -300    1    100    1    300    10    0    0    0    0    0    0    0    0    0    0    0;
    3    0    0    300    -300    1    100    1    270    10    0    0    0    0    0    0    0    0    0    0    0;
];

% branch data
%    fbus    tbus    r    x    b    rateA    rateB    rateC    ratio    angle    status    angmin    angmax    P    Q
mpc.branch = [
    1    4    0    0.0576    0    250    250    250    0    0    1    -360    360    0    0;
    4    5    0.017    0.092    0.158    250    250    250    0    0    1    -360    360    0    0;
    5    6    0.039    0.17    0.183    250    250    250    0    0    1    -360    360    0    0;
    3    6    0    0.0586    0    250    250    250    0    0    1    -360    360    0    0;
    6    7    0.0119    0.1008    0.1045    250    250    250    0    0    1    -360    360    0    0;
    7    8    0.0085    0.072    0.0745    250    250    250    0    0    1    -360    360    0    0;
    8    2    0    0.0625    0    250    250    250    0    0    1    -360    360    0    0;
    8    9    0.032    0.161    0.153    250    250    250    0    0    1    -360    360    0    0;
    4    9    0.01    0.085    0.088    250    250    250    0    0    1    -360    360    0    0;
];

% generator cost data
%    2    startup    shutdown    n    c(n-1)    ...    c0
mpc.gencost = [
    2    0    0    3    0    25    0;
    2    0    0    3    0    30    0;
    2    0    0    3    0    35    0;
];
