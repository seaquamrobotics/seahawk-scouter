while (true) {          
        LeftMotor.spin(directionType::fwd, (Controller1.Axis3.value() + Controller1.Axis4.value())/2, velocityUnits::pct); //(Axis3+Axis4)/2;
        RightMotor.spin(directionType::fwd, (Controller1.Axis3.value() - Controller1.Axis4.value())/2, velocityUnits::pct);//(Axis3-Axis4)/2;

        task::sleep(20);
    } 