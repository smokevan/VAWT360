import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# Global variables for application and UI
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)

# Handler lists
_handlers = []

def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # Create a command definition
        cmdDef = _ui.commandDefinitions.itemById('createTurbine')
        if not cmdDef:
            cmdDef = _ui.commandDefinitions.addButtonDefinition('createTurbine', 'Create Turbine', 'Create a vertical axis wind turbine')

        # Connect to the command created event
        onCommandCreated = TurbineCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command
        cmdDef.execute()

        # Prevent script termination
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class TurbineCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.CommandCreatedEventArgs.cast(args)
            inputs = cmd.command.commandInputs

            # Create a new group for drag turbine parameters
            dragTurbineParametersGroup = inputs.addGroupCommandInput('dragTurbineParameters', 'Drag Turbine Parameters')
            dragTurbineParametersInputs = dragTurbineParametersGroup.children
            dragTurbineParametersInputs.addValueInput('shaftDiameter', 'Shaft Diameter', 'in', adsk.core.ValueInput.createByString('1 in'))
            dragTurbineParametersInputs.addValueInput('outerDiameter', 'Outer Diameter', 'in', adsk.core.ValueInput.createByString('10 in'))
            dragTurbineParametersInputs.addValueInput('bladeThickness', 'Blade Thickness', 'in', adsk.core.ValueInput.createByString('0.125 in'))
            dragTurbineParametersInputs.addValueInput('bladeDepth', 'Blade Depth', 'in', adsk.core.ValueInput.createByString('1 in'))
            dragTurbineParametersInputs.addValueInput('turbineHeight', 'Turbine Height', 'in', adsk.core.ValueInput.createByString('10 in'))
            dragTurbineParametersInputs.addIntegerSpinnerCommandInput('bladeCount', 'Blade Count', 1, 100, 1, 2)
            dragTurbineParametersInputs.addIntegerSpinnerCommandInput('twistCount', 'Twist Count', 1, 100, 1, 1)

            # Create a new group for airfoil turbine parameters
            airfoilTurbineParametersGroup = inputs.addGroupCommandInput('airfoilTurbineParameters', 'Airfoil Turbine Parameters')
            airfoilTurbineParametersInputs = airfoilTurbineParametersGroup.children

            airfoilTurbineParametersInputs.addStringValueInput('nacaProfile', 'NACA Profile', ('0015'))
            airfoilTurbineParametersInputs.addIntegerSpinnerCommandInput('airfoilCount', 'Airfoil Count', 1, 100, 1, 3)
            airfoilTurbineParametersInputs.addValueInput('chordLength', 'Chord Length', 'in', adsk.core.ValueInput.createByString('3.0 in'))
            airfoilTurbineParametersInputs.addValueInput('distanceFromCenter', 'Distance from Center', 'in', adsk.core.ValueInput.createByString('15.0 in'))

            # Connect to command related events
            onExecute = TurbineCommandExecuteHandler()
            cmd.command.execute.add(onExecute)
            _handlers.append(onExecute)

            onDestroy = TurbineCommandDestroyHandler()
            cmd.command.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        except Exception as e:
            _ui.messageBox('Failed to create command: {}'.format(str(e)))


class TurbineCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            # Retrieve the groups
            dragTurbineParametersInputs = inputs.itemById('dragTurbineParameters').children
            airfoilTurbineParametersInputs = inputs.itemById('airfoilTurbineParameters').children

            # Retrieve and cast the input values to float for precision
            holeDiameter = float(0.0575*25.4)
            shaftDiameter = float(dragTurbineParametersInputs.itemById('shaftDiameter').value)
            outerDiameter = float(dragTurbineParametersInputs.itemById('outerDiameter').value)
            bladeThickness = float(dragTurbineParametersInputs.itemById('bladeThickness').value)
            bladeDepth = float(dragTurbineParametersInputs.itemById('bladeDepth').value)
            turbineHeight = float(dragTurbineParametersInputs.itemById('turbineHeight').value)
            bladeCount = int(dragTurbineParametersInputs.itemById('bladeCount').value)  # Blade count is an integer

            # Retrieve and cast the airfoil parameters
            nacaProfile = airfoilTurbineParametersInputs.itemById('nacaProfile').value
            halfCosineSpacing = True
            numPoints = int(100)
            finiteThicknessTE = False
            airfoilCount = int(airfoilTurbineParametersInputs.itemById('airfoilCount').value)
            chordLength = float(airfoilTurbineParametersInputs.itemById('chordLength').value)
            distanceFromCenter = float(airfoilTurbineParametersInputs.itemById('distanceFromCenter').value)
            twistCount = int(dragTurbineParametersInputs.itemById('twistCount').value)  # Twist count is an integer

            # Create the turbine components
            createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount, nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, airfoilCount)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class TurbineCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        adsk.terminate()

def createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount, nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, airfoilCount):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        rootComp = design.rootComponent
        occs = rootComp.occurrences
        newOcc = occs.addNewComponent(adsk.core.Matrix3D.create())
        newComp = newOcc.component 
        newComp.name = "DragTurbine" 
        # Now, use 'newComp' for all operations, like sketches, extrusions, etc.
        # For example, creating a sketch in the new component context
        sketches = newComp.sketches
        xzPlane = newComp.xZConstructionPlane
        sketchbbase = sketches.add(xzPlane)

        # Create circles
        centerPoint = adsk.core.Point3D.create(0, 0, 0)
        shaftCircle = sketchbbase.sketchCurves.sketchCircles.addByCenterRadius(centerPoint, shaftDiameter / 2.0)

        # Calculate hexagon vertices and create an inscribed hexagon
        radius = holeDiameter / 2.0
        hexagonPoints = []
        for i in range(6):
            angle_deg = 60 * i - 30  # -30 to start the first point at the top
            angle_rad = math.radians(angle_deg)
            x = centerPoint.x + radius * math.cos(angle_rad)
            y = centerPoint.y + radius * math.sin(angle_rad)
            hexagonPoints.append(adsk.core.Point3D.create(x, y, 0))

        # Add sketch points for hexagon vertices
        sketchPoints = sketchbbase.sketchPoints
        for point in hexagonPoints:
            sketchPoints.add(point)

        # Connect the hexagon points with lines
        for i in range(6):
            start_point = hexagonPoints[i]
            end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
            sketchbbase.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)

        extrudes = newComp.features.extrudeFeatures
        shaftprofile = sketchbbase.profiles.item(0)
        extrudeInput = extrudes.createInput(shaftprofile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(turbineHeight))
        extrude = extrudes.add(extrudeInput)

        arcPoint = adsk.core.Point3D.create((-(((((outerDiameter / 4.0) ** 2) / bladeDepth) + bladeDepth) / 2.0) + bladeDepth), (outerDiameter / 4.0), 0)
        sweepAngle = 2 * math.asin(outerDiameter / ((2 * ((outerDiameter / 4.0) ** 2) / bladeDepth) + bladeDepth))
        arc = sketchbbase.sketchCurves.sketchArcs.addByCenterStartSweep(arcPoint, centerPoint, sweepAngle)

        # Define the offset using BladeThickness
        offsetValue = adsk.core.ValueInput.createByReal(-bladeThickness)
        basePoint = arc.startSketchPoint.geometry  # Using the start point of the arc for the base point

        # Add the offset constraint to create offset arc
        geometricConstraints = sketchbbase.geometricConstraints
        offsetConstraint = geometricConstraints.addOffset([arc], offsetValue, basePoint)

        if offsetConstraint and offsetConstraint.childCurves:
            offsetArc = offsetConstraint.childCurves[0]  # Assuming the first curve is the offset arc

            # Connect the end points of the original and the offset arc with a line
            sketchbbase.sketchCurves.sketchLines.addByTwoPoints(arc.endSketchPoint, offsetArc.endSketchPoint)

        # Create a sketch on the XY plane for the vertical line
        sketchesXY = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketchXY = sketchesXY.add(xyPlane)

        # Calculate the end point of the vertical line based on turbineHeight
        startPoint = adsk.core.Point3D.create(0, 0, 0)  # Reusing the centerPoint as the start point for the vertical line
        endPoint = adsk.core.Point3D.create(0, turbineHeight, 0)  # n units up along the Y-axis

        # Add the vertical line to the sketch
        sketchXY.sketchCurves.sketchLines.addByTwoPoints(startPoint, endPoint)

        # Assume 'sketch' is already defined and contains your arcs and connecting line
        # Assume 'sketchXY' contains the vertical line for the sweep path

        # Step 1: Identify the profile formed by the two arcs and connecting line
        # This step is conceptual; you need to identify the correct profile in your sketch
        profileToSweep = sketchbbase.profiles.item(0)  # Example: Selecting the first profile
        
        # Step 2: Create the path for the sweep
        # Assuming 'sketchXY' contains the vertical line for the path
        path = newComp.features.createPath(sketchXY.sketchCurves.sketchLines.item(0))  # Selecting the first line as the path

        # Step 3: Perform the sweep with the twist angle
        sweeps = newComp.features.sweepFeatures
        sweepInput = sweeps.createInput(profileToSweep, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        twistAngle = adsk.core.ValueInput.createByString(f"{(-360 / bladeCount)*twistCount} deg")
        sweepInput.twistAngle = twistAngle
        sweep = sweeps.add(sweepInput)

        # After creating the sweep feature for a blade
        sweepFeature = sweep  # Assuming 'sweep' is the variable holding the last created sweep feature

        # Collect the sweep feature in an ObjectCollection
        inputEntities = adsk.core.ObjectCollection.create()
        inputEntities.add(sweepFeature)

        # Get the Y axis as the axis of rotation for the circular pattern
        yAxis = newComp.yConstructionAxis

        # Create the circular pattern
        circularPatterns = newComp.features.circularPatternFeatures
        circularPatternInput = circularPatterns.createInput(inputEntities, yAxis)
        circularPatternInput.quantity = adsk.core.ValueInput.createByReal(bladeCount)
        circularPatternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')  # Full circle
        circularPattern = circularPatterns.add(circularPatternInput)

        def naca4(number, n, finite_TE, half_cosine_spacing):
            m = int(number[0]) / 100.0  # Maximum camber
            p = int(number[1]) / 10.0   # Location of maximum camber
            t = int(number[2:]) / 100.0 # Maximum thickness
    
            # Define the thickness distribution function (same as before)
            def thickness(x):
                a0 = 0.2969
                a1 = -0.126
                a2 = -0.3516
                a3 = 0.2843
                a4 = -0.1015 if finite_TE else -0.1036  # Adjust for finite thickness at trailing edge
        
                return 5 * t * (a0 * math.sqrt(x) + a1 * x + a2 * x**2 + a3 * x**3 + a4 * x**4)
    
            # Define a function to calculate the camber line and its slope
            def camber_line(x):
                if x < p:
                    return m / p**2 * (2 * p * x - x**2)
                elif x == p:
                    return m
                else:
                    return m / (1 - p)**2 * ((1 - 2*p) + 2*p*x - x**2)
    
            def camber_slope(x):
                if x < p:
                    return (2*m / p**2) * (p - x)
                else:
                    return (2*m / (1 - p)**2) * (p - x)
    
            # Generate the x coordinates
            x = [i / n for i in range(n + 1)] if not half_cosine_spacing else [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    
            # Calculate the camber line and its slope for each x
            yc = [camber_line(xi) for xi in x]
            dyc_dx = [camber_slope(xi) for xi in x]
            theta = [math.atan(dy) for dy in dyc_dx]
    
            # Calculate the thickness distribution for each x
            yt = [thickness(xi) for xi in x]
    
            # Calculate upper and lower surface points
            xu = [xi - yt[i] * math.sin(theta[i]) for i, xi in enumerate(x)]
            yu = [yc[i] + yt[i] * math.cos(theta[i]) for i in range(len(x))]
            xl = [xi + yt[i] * math.sin(theta[i]) for i, xi in enumerate(x)]
            yl = [yc[i] - yt[i] * math.cos(theta[i]) for i in range(len(x))]
    
            # Combine the upper and lower points
            X = xu + xl[::-1]
            Y = yu + yl[::-1]
    
            return X, Y

        # Method to Create Airfoil Sketch
        def createNacaAirfoil(nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, turbineHeight, airfoilCount):
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = app.activeProduct
            rootComp = design.rootComponent
            xzPlane = rootComp.xZConstructionPlane
            xyPlane = rootComp.xYConstructionPlane

            airfoilComp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            airfoilComp.component.name = "Airfoils"

            # Generate NACA airfoil points
            X, Z = naca4(nacaProfile, int(numPoints), finiteThicknessTE, halfCosineSpacing)

            # Adjust points based on chord length, center the airfoil, and position it for clockwise rotation
                        # Adjust points based on chord length, center the airfoil, and position it for clockwise rotation
            points = []
            for x, z in zip(X, Z):
                # Flip the airfoil by reversing the x-coordinate around its central axis (chord/2)
                x_flipped = (chordLength / 2) - (x * chordLength - (chordLength / 2))
                x_flipped -= chordLength / 2  # Shift along the x-axis by half the chord length
                z_shifted = turbineHeight / 2  # Position the airfoil at half the turbineHeight
                y_height = z * chordLength  #  Shift along the Y-axis for distanceFromCenter
                points.append(adsk.core.Point3D.create(x_flipped, y_height, z_shifted))

            # Create the sketch and connect points with lines
            sketches = airfoilComp.component.sketches
            sketchfoil = sketches.add(xzPlane)
            # Here we ensure the points are connected in their original order to maintain the profile shape
            for i in range(len(points) - 1):
                sketchfoil.sketchCurves.sketchLines.addByTwoPoints(points[i], points[i + 1])

            # Optionally, close the loop, connecting the last point back to the first
            sketchfoil.sketchCurves.sketchLines.addByTwoPoints(points[-1], points[0])

            # Extrude the airfoil profile symmetrically
            extrudeDistance = ((0.5*turbineHeight)+0.3)
            profiles = sketchfoil.profiles
            if profiles.count > 0:
                profileToExtrude = profiles.item(0)  # Assuming the airfoil profile is the only one in the sketch

                # Get the extrude features collection
                extrudes = airfoilComp.component.features.extrudeFeatures

                # Create an extrusion input to add to the collection
                extrudeInput = extrudes.createInput(profileToExtrude, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
                # Set the extrusion distance symmetrically
                distance = adsk.core.ValueInput.createByString(f'{extrudeDistance} in')  # Half distance for symmetric extrusion
                extrudeInput.setSymmetricExtent(distance, True)
        
            # Create the extrusion
            extrudeFeature = extrudes.add(extrudeInput)

            sketchbCone = sketches.add(xyPlane)
            sketchtCone = sketches.add(xyPlane)
            bCircleRad = 0.05*25.4  # Radius in inches
            tCircleRad = 0.0375*25.4  # Radius in inches
            bPointBottom = adsk.core.Point3D.create(0, -0.05*25.4, 0)  # Convert -0.5 inches to millimeters
            tPointBottom = adsk.core.Point3D.create(0, (turbineHeight+(0.05*25.4)), 0)  # Convert (turbineHeight + 0.5) inches to millimeters

            tConeBottom = sketchtCone.sketchCurves.sketchCircles.addByCenterRadius(tPointBottom, bCircleRad)
            bConeBottom = sketchbCone.sketchCurves.sketchCircles.addByCenterRadius(bPointBottom, bCircleRad)

            def calculate_thickness(x, number, finite_TE):
                t = int(number[2:]) / 100.0  # Maximum thickness

                a0 = 0.2969
                a1 = -0.126
                a2 = -0.3516
                a3 = 0.2843
                a4 = -0.1015 if finite_TE else -0.1036  # Adjust for finite thickness at trailing edge

                return 5 * t * (a0 * math.sqrt(x) + a1 * x + a2 * x**2 + a3 * x**3 + a4 * x**4)
            
            z_dist = calculate_thickness(0.5, nacaProfile, finiteThicknessTE)
            
            bPointTop = adsk.core.Point3D.create(0, -0.05*25.4, (z_dist*chordLength)+(0.0125*25.4))
            tPointTop = adsk.core.Point3D.create(0, (turbineHeight+(0.05*25.4)), (z_dist*chordLength)+(0.0125*25.4))
            
            bConeTop = sketchbCone.sketchCurves.sketchCircles.addByCenterRadius(bPointTop, tCircleRad)
            tConeTop = sketchtCone.sketchCurves.sketchCircles.addByCenterRadius(tPointTop, tCircleRad)

            # Create a new loft feature
            loftFeatures = airfoilComp.component.features.loftFeatures

            # Create a new loft input for sketchbCone
            loftInputB = loftFeatures.createInput(adsk.fusion.FeatureOperations.JoinFeatureOperation)

            # Add the two circles in sketchbCone to the loft input
            loftInputB.loftSections.add(sketchbCone.profiles.item(0))
            loftInputB.loftSections.add(sketchbCone.profiles.item(1))

            # Create the loft feature for sketchbCone
            loftFeatureB = loftFeatures.add(loftInputB)

            # Create a new loft input for sketchtCone
            loftInputT = loftFeatures.createInput(adsk.fusion.FeatureOperations.JoinFeatureOperation)

            # Add the two circles in sketchtCone to the loft input
            loftInputT.loftSections.add(sketchtCone.profiles.item(0))
            loftInputT.loftSections.add(sketchtCone.profiles.item(1))

            # Create the loft feature for sketchtCone
            loftFeatureT = loftFeatures.add(loftInputT)

            def coneHexHole(sketchName, z_dist, chordLength, y_shift):
                hexagonPoints = []
                for i in range(6):
                    angle_deg = 60 * i - 30  # -30 to start the first point at the top
                    angle_rad = math.radians(angle_deg)
                    x = centerPoint.x + radius * math.cos(angle_rad)
                    y = centerPoint.y + radius * math.sin(angle_rad)
                    hexagonPoints.append(adsk.core.Point3D.create(x, y+y_shift, (z_dist*chordLength)+(0.0125*25.4)))

                # Add sketch points for hexagon vertices
                sketchPoints = sketchName.sketchPoints
                for point in hexagonPoints:
                    sketchPoints.add(point)

                # Connect the hexagon points with lines
                for i in range(6):
                    start_point = hexagonPoints[i]
                    end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
                    sketchName.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)
            
            coneHexHole(sketchbCone, z_dist, chordLength, -0.05*25.4)
            coneHexHole(sketchtCone, z_dist, chordLength, (turbineHeight+(0.05*25.4)))

            # Get the extrude features collection
            extrudeFeatures = airfoilComp.component.features.extrudeFeatures

            # Define the distance for the extrusion
            distance = adsk.core.ValueInput.createByReal(-z_dist-(0.025*25.4))

            # Create an extrusion input for each sketch
            for sketch in [sketchbCone, sketchtCone]:
                # Get the profile defined by the hexagon
                profile = sketch.profiles.item(1)

                # Create an extrusion input
                extrudeInput = extrudeFeatures.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)

                # Set the distance for the extrusion
                extrudeInput.setDistanceExtent(False, distance)

                # Create the extrusion
                extrudeFeature = extrudeFeatures.add(extrudeInput)

            # Assume extrudeFeature is the last created extrusion
            extrudeFeature = airfoilComp.component.features.extrudeFeatures.item(airfoilComp.component.features.extrudeFeatures.count - 1)

            # Create an ObjectCollection for the body/bodies produced by the extrusion
            bodiesCollection = adsk.core.ObjectCollection.create()

            for body in extrudeFeature.bodies:
                bodiesCollection.add(body)
            
            for body in loftFeatureB.bodies:
                bodiesCollection.add(body)

            for body in loftFeatureT.bodies:
                bodiesCollection.add(body)

            yAxis = airfoilComp.component.yConstructionAxis

            transform = adsk.core.Matrix3D.create()
            transform.translation = adsk.core.Vector3D.create(0, 0, -distanceFromCenter)
            moveFeatures = airfoilComp.component.features.moveFeatures
            moveInput = moveFeatures.createInput(bodiesCollection, transform)
            moveFeatures.add(moveInput)

            # Create the circular pattern
            circularPatterns = airfoilComp.component.features.circularPatternFeatures
            patternInput = circularPatterns.createInput(bodiesCollection, yAxis)
            patternInput.quantity = adsk.core.ValueInput.createByReal(airfoilCount)
            patternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')  # Distribute around a full circle
            patternInput.isSymmetric = False  # Adjust if your design requires symmetric distribution

            # Create the pattern
            circularPatternFeature = circularPatterns.add(patternInput)

        createNacaAirfoil(nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, turbineHeight, airfoilCount)

        def create_connectors(connectorDiameter, turbineHeight, airfoilCount):
            
            def create_bottom_connector(connectorDiameter, airfoilCount):
                # Get the active product
                product = adsk.core.Application.get().activeProduct
                # Get the root component of the active design.
                rootComp = product.rootComponent
                xzPlane = rootComp.xZConstructionPlane
                yzPlane = rootComp.yZConstructionPlane
                bconnectorComp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                bconnectorComp.component.name = "BottomConnector"
                # Create a new sketch on the xz plane.
                sketches = bconnectorComp.component.sketches
                sketchbbase = sketches.add(xzPlane)

                hexdia = 0.0575*25.4
                y_shift = -0.05*25.4

                hexagonPoints = []
                for i in range(6):
                    angle_deg = 60 * i - 30  # -30 to start the first point at the top
                    angle_rad = math.radians(angle_deg)
                    x = centerPoint.x + (hexdia/2) * math.cos(angle_rad)
                    y = centerPoint.y + (hexdia/2) * math.sin(angle_rad)
                    hexagonPoints.append(adsk.core.Point3D.create(x, y, 0))

                # Add sketch points for hexagon vertices
                sketchPoints = sketchbbase.sketchPoints
                
                for point in hexagonPoints:
                    sketchPoints.add(point)

                # Connect the hexagon points with lines
                for i in range(6):
                    start_point = hexagonPoints[i]
                    end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
                    sketchbbase.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)

                # Draw a circle with the specified diameter.
                circles = sketchbbase.sketchCurves.sketchCircles
                base = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), connectorDiameter/2)
                # Get the profile corresponding to the circle
                profile = sketchbbase.profiles.item(1)  # Select the first profile
                # Get extrude features
                extrudes = bconnectorComp.component.features.extrudeFeatures
                # Create an extrusion input
                extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                # Define the distance for the extrusion
                distance = adsk.core.ValueInput.createByString('-1 in')
                # Set the distance extent to be single direction
                extInput.setDistanceExtent(False, distance)
                # Create the extrusion
                extrudes.add(extInput)

                sketchbhex = sketches.add(yzPlane)
                hexagonPoints = []
                for i in range(6):
                    angle_deg = 60 * i - 30  # -30 to start the first point at the top
                    angle_rad = math.radians(angle_deg)
                    x = centerPoint.x + (hexdia/2) * math.sin(angle_rad)
                    y = centerPoint.y + (hexdia/2) * math.cos(angle_rad)
                    hexagonPoints.append(adsk.core.Point3D.create(x, y+y_shift, -connectorDiameter/2))

                # Add sketch points for hexagon vertices
                sketchPoints = sketchbhex.sketchPoints
                
                for point in hexagonPoints:
                    sketchPoints.add(point)

                # Connect the hexagon points with lines
                for i in range(6):
                    start_point = hexagonPoints[i]
                    end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
                    sketchbhex.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)
                
                profilehex = sketchbhex.profiles.item(0)

                extInputHole = extrudes.createInput(profilehex, adsk.fusion.FeatureOperations.CutFeatureOperation)
                holedepth = adsk.core.ValueInput.createByReal(connectorDiameter/4)
                extInputHole.setDistanceExtent(False, holedepth)
                holeExtrude = bconnectorComp.component.features.extrudeFeatures.add(extInputHole)


                sketchbscrew = sketches.add(xzPlane)

                holecircles = sketchbscrew.sketchCurves.sketchCircles
                holepoint = adsk.core.Point3D.create((-connectorDiameter*(1/3)), 0, 0)
                hole = holecircles.addByCenterRadius(holepoint, 0.25)

                profilehole = sketchbscrew.profiles.item(0)
                extInputScrew = extrudes.createInput(profilehole, adsk.fusion.FeatureOperations.CutFeatureOperation)
                screwdepth = adsk.core.ValueInput.createByString('-0.25 in')
                extInputScrew.setDistanceExtent(False, screwdepth)
                screwExtrude = bconnectorComp.component.features.extrudeFeatures.add(extInputScrew)


                #create the circular pattern
                yAxis = bconnectorComp.component.yConstructionAxis
                circularPatterns = bconnectorComp.component.features.circularPatternFeatures
                inputEntities = adsk.core.ObjectCollection.create()
                inputEntities.add(holeExtrude)
                inputEntities.add(screwExtrude)

                patternInput = circularPatterns.createInput(inputEntities, yAxis)
                patternInput.quantity = adsk.core.ValueInput.createByReal(airfoilCount)
                patternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
                circularPattern = circularPatterns.add(patternInput)
            
            def create_top_connector(connectorDiameter,turbineHeight, airfoilCount):
                # Get the active product
                product = adsk.core.Application.get().activeProduct
                # Get the root component of the active design.
                rootComp = product.rootComponent
                xzPlane = rootComp.xZConstructionPlane
                yzPlane = rootComp.yZConstructionPlane
                tconnectorComp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                tconnectorComp.component.name = "TopConnector"
                # Create a new sketch on the xz plane.
                sketches = tconnectorComp.component.sketches
                sketchtbase = sketches.add(xzPlane)

                hexdia = 0.0575*25.4
                y_shift = 0.05*25.4

                # Draw a circle with the specified diameter.
                circles = sketchtbase.sketchCurves.sketchCircles
                base = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, turbineHeight), connectorDiameter/2)
                # Get the profile corresponding to the circle
                profile = sketchtbase.profiles.item(0)  # Select the first profile
                # Get extrude features
                extrudes = tconnectorComp.component.features.extrudeFeatures
                # Create an extrusion input
                extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                # Define the distance for the extrusion
                distance = adsk.core.ValueInput.createByString('1 in')
                # Set the distance extent to be single direction
                extInput.setDistanceExtent(False, distance)
                # Create the extrusion
                extrudes.add(extInput)

                hexagonPoints = []
                for i in range(6):
                    angle_deg = 60 * i - 30  # -30 to start the first point at the top
                    angle_rad = math.radians(angle_deg)
                    x = centerPoint.x + (hexdia/2) * math.cos(angle_rad)
                    y = centerPoint.y + (hexdia/2) * math.sin(angle_rad)
                    hexagonPoints.append(adsk.core.Point3D.create(x, y, turbineHeight))

                # Add sketch points for hexagon vertices
                sketchPoints = sketchtbase.sketchPoints
                
                for point in hexagonPoints:
                    sketchPoints.add(point)

                # Connect the hexagon points with lines
                for i in range(6):
                    start_point = hexagonPoints[i]
                    end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
                    sketchtbase.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)

                profileshaft = sketchtbase.profiles.item(1)

                extInputHex = extrudes.createInput(profileshaft, adsk.fusion.FeatureOperations.CutFeatureOperation)
                # Define the distance for the extrusion
                distance = adsk.core.ValueInput.createByString('0.75 in')
                # Set the distance extent to be single direction
                extInputHex.setDistanceExtent(False, distance)
                # Create the extrusion
                extrudes.add(extInputHex)

                topscrew = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, turbineHeight+(0.1*25.4)), 0.25)
                profiletop = sketchtbase.profiles.item(0)

                extInputTop = extrudes.createInput(profiletop, adsk.fusion.FeatureOperations.CutFeatureOperation)
                # Define the distance for the extrusion
                distance = adsk.core.ValueInput.createByString('-0.25 in')
                # Set the distance extent to be single direction
                extInputTop.setDistanceExtent(False, distance)
                # Create the extrusion
                extrudes.add(extInputTop)


                sketchthex = sketches.add(yzPlane)
                hexagonPoints = []
                for i in range(6):
                    angle_deg = 60 * i - 30  # -30 to start the first point at the top
                    angle_rad = math.radians(angle_deg)
                    x = centerPoint.x + (hexdia/2) * math.sin(angle_rad)
                    y = centerPoint.y + (hexdia/2) * math.cos(angle_rad)
                    hexagonPoints.append(adsk.core.Point3D.create(x, y+y_shift+turbineHeight, -(connectorDiameter/2)))

                # Add sketch points for hexagon vertices
                sketchPoints = sketchthex.sketchPoints
                
                for point in hexagonPoints:
                    sketchPoints.add(point)

                # Connect the hexagon points with lines
                for i in range(6):
                    start_point = hexagonPoints[i]
                    end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
                    sketchthex.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)
                
                profilehex = sketchthex.profiles.item(0)

                extInputHole = extrudes.createInput(profilehex, adsk.fusion.FeatureOperations.CutFeatureOperation)
                holedepth = adsk.core.ValueInput.createByReal(connectorDiameter/4)
                extInputHole.setDistanceExtent(False, holedepth)
                holeExtrude = tconnectorComp.component.features.extrudeFeatures.add(extInputHole)


                sketchtscrew = sketches.add(xzPlane)

                holecircles = sketchtscrew.sketchCurves.sketchCircles
                holepoint = adsk.core.Point3D.create((-connectorDiameter*(1/3)), 0, turbineHeight)
                hole = holecircles.addByCenterRadius(holepoint, 0.25)

                profilehole = sketchtscrew.profiles.item(0)
                extInputScrew = extrudes.createInput(profilehole, adsk.fusion.FeatureOperations.CutFeatureOperation)
                screwdepth = adsk.core.ValueInput.createByString('0.25 in')
                extInputScrew.setDistanceExtent(False, screwdepth)
                screwExtrude = tconnectorComp.component.features.extrudeFeatures.add(extInputScrew)


                #create the circular pattern
                yAxis = tconnectorComp.component.yConstructionAxis
                circularPatterns = tconnectorComp.component.features.circularPatternFeatures
                inputEntities = adsk.core.ObjectCollection.create()
                inputEntities.add(holeExtrude)
                inputEntities.add(screwExtrude)

                patternInput = circularPatterns.createInput(inputEntities, yAxis)
                patternInput.quantity = adsk.core.ValueInput.createByReal(airfoilCount)
                patternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
                circularPattern = circularPatterns.add(patternInput)      
            create_bottom_connector(connectorDiameter, airfoilCount)
            create_top_connector(connectorDiameter, turbineHeight, airfoilCount)
                

        create_connectors(0.3*24.5, turbineHeight, airfoilCount)
      
    except Exception as e:
        ui = adsk.core.Application.get().userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        if _ui:
            for handler in _handlers:
                _ui.messageBox(str(handler))
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))