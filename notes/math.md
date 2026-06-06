# Math notes for some of the controller placement calculations

---

## Placing the FK spine joints
For the FK spine, we're cheating a bit and just taking the position of the 2nd and 3d bone up from the spine base, averaging their position, and sticking the a single mid FK joint/control there.

Ideally we'd make a calculation to find a middle point in distance of the IK chain and place an FK joint there. Maybe do multiple FK controls for a super windy spine, but brother I got so much to do and I have a TODO to maybe look into it later

## Rotating the foot controller to match the flare out of the foot

We want the foot controller to offset group to sit at the ankle and match the flareout angle of ankle twist, but we'd like the Y axis to point up so in object space the foot control doesn't go up diagonally because of the pitch inherent in the ankle joint.

This boils down to just wanting to rotate around the world Y axis.

We calculate a vector going in the bone direction by just substracting the location of the ankle joint from the location of the ball joint.
We want the rotation of that vector with respect to the world Y axis.
We don't care about the pitch, so if we project that bone vector onto the xz plane that is all we need to calculate the rotation.

In a general scenario, we'd want to project the bone vector onto the plane doing something like
Projected_BoneVec = BoneVec - (BoneVec · PlaneNormal)*PlaneNormal
But since we're just projecting onto the world xz plane. We get to do it easily.

The dot product algebraic formula is
A · B = (A_x * B_x) + (A_y * B_y) + (A_z * B_z)
and since we're working with a easy [0, 1, 0] normal, this is just BoneVec.y * 1
then again since we're just multiplying that factor into that [0, 1, 0] we get [0, BoneVec.y, 0]

So we just need to yeet out the y component of the bone vector to get the projection onto the world xz plane.

Then to get the rotation out of that projected vector we pull out the trig for an atan2()

The default orientation is facing positive Z, so we want that to be the neutral rotation (0). 
Go back to middle school and remeber tangent on the unit circle is Tripping On Acid where our adjacent side we want to be the z component since that's where we're facing.

atan2 takes the arguments (opposite, adjacent) so wham bam atan2(dx, dz) gives us that angle the bone is rotated by.

Then we can just snap the foot controller offset group to the ankle, crank it, and move the control vertices closer to the floor.


# Placement of the Knee pole vector
What we learned in class was to find the centroid with a point constraint with 3 bosses of the hip, knee, and ankle.
Then if we aim the control towards the knee, we can move in object space without losing coplanarity.
The issue is that the local axes are not going to point cleanly out in front of the knee and I don't like it.

So instead if we take the vector from the hip to the ankle and the vector from the hip to the knee and then project hipKnee onto hipAnkle we can get a position that is coplanar and directly behind the knee.
Then we can move in the direction of the knee joint, overshoot, and be in front.


## Clavicle Controller Rotation/Offset

The clavicle controller is a little arrow that we want pointing up out of the shoulder.
We make the curve pointing up in world Y, but when we group over align the controller to the clavicle, +Y means something different.
We want to have the arrow pointing in the axis closest to world up, and then we want to translate the control vertices "up" in that direction as well to stop clipping the geometry.
In class we made skeletons that had Y pointing vaguely forward, but I don't know how reliable that is.

To orient the clavicle arrow control dynamically without making assumptions about how the skeleton was built, we can look at the joint's **World Matrix**. 

Row 0, Row 1, and Row 2 of the matrix represent the local X, Y, and Z axis direction vectors in world space. By taking the dot product of these local vectors with a given target world direction (like `(0, 1, 0)` for Up) we can find which local axis is the closest to "Up"
So once we know which local axis is the best match, we do 2 things
1) check this switch statement that maps out how to rotate (0, 1, 0) to that target axis.
2) move up by some factor of that local axis hoping the geometry doesn't clip. Prayge
